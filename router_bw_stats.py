import time
import json
import re
import urllib2
import redis
import sys


class RouterFlow:
    def __init__(self):
        self.user = 'admin'
        self.pwd = 'password'
        self.host = '192.168.1.1'
        self.sleep_time = 1  # Seconds
        self.bw_avg_window = 1  # Compute avg of last n values

        self.setup_redis()
        self.setup_urlopener()

        # Keep track of past bandwidth rate data
        self.past_rates = []

    def setup_urlopener(self):
        passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
        passman.add_password(None, self.host, self.user, self.pwd)
        authhandler = urllib2.HTTPBasicAuthHandler(passman)
        self.opener = urllib2.build_opener(authhandler)

    def setup_redis(self):
        self.redis = redis.Redis()
        if self.redis.ping() is False:
            print "Error, Redis not running"
            sys.exit(1)

    def get_device_names(self):
        all_devices = dict()
        while True:
            try:
                resp = self.opener.open('http://192.168.1.1/QOS_device_info.htm'
                                        '?ts=%d'.format(int(time.time() * 1000)))
                if resp.getcode() != 200:
                    raise Exception("Non-200 response")
            except Exception as e:
                print "Didn't work, trying again. ", str(e)
                continue

            results = re.findall(r'mac:"(?P<mac>.*?)", ip:"(?P<ip>.*?)", '
                                 'name:"(?P<hostname>.*?)", ', resp.read())
            for mac, ip, hostname in results:
                all_devices[mac.lower()] = hostname

            return all_devices

    def _call(self, url):
        while True:
            try:
                resp = self.opener.open(url)
                if resp.getcode() != 200:
                    raise Exception("Non-200 response")
                resp_json = json.loads(resp.read())
            except Exception as e:
                print "Didn't work, trying again. ", str(e)
                continue

            return resp_json

    def get_current_flow(self):
        current_flows = dict()
        response = self._call('http://192.168.1.1/cgi-bin/'
                              'ozker/api/flows?ts=%d'.format(
                                  int(time.time() * 1000)))
        for flow in response['flows']:
            current_flows[flow['uid']] = dict(up_bytes=flow['up_bytes'],
                                              down_bytes=flow['down_bytes'],
                                              mac=flow['mac'])
        return current_flows

    def add_flow(self, summary, flow):
        mac = flow["mac"]
        up_bytes = flow["up_bytes"]
        down_bytes = flow["down_bytes"]

        if mac not in summary.keys():
            summary[mac] = dict(down_bytes=down_bytes,
                                up_bytes=up_bytes)
        else:
            summary[mac]['up_bytes'] += up_bytes
            summary[mac]['down_bytes'] += down_bytes

    def get_summary(self, flows):
        summary = dict()

        for n, flow in flows.items():
            # n = 1234 (flow number)
            # data = {'mac': u'64:bc:0c:67:f9:67',
            # 'down_bytes': 216, 'up_bytes': 310}
            self.add_flow(summary, flow)

        return summary

    def refresh_summary(self):
        current_flows = self.get_current_flow()
        summary = self.get_summary(current_flows)
        return summary

    def calc_diff(self, old, new):
        rate = dict()

        for mac in new.keys():
            try:
                diff_up_kbps = (new[mac]['up_bytes'] -
                                old[mac]['up_bytes']) / 1024.0 / self.sleep_time
                diff_down_kbps = (new[mac]['down_bytes'] -
                                  old[mac]['down_bytes']) / 1024.0 / self.sleep_time
                rate[mac] = dict(up_kbps=diff_up_kbps,
                                 down_kbps=diff_down_kbps)
            except KeyError:
                # Some device dissapreared. Fine
                pass

        return rate

    def get_avg_bw_rate(self):
        avg_rate = dict()

        # Calc sum
        for rate in self.past_rates:
            for mac, stats in rate.items():
                if mac not in avg_rate.keys():
                    avg_rate[mac] = dict(up_kbps=stats['up_kbps'],
                                         down_kbps=stats['down_kbps'])
                else:
                    avg_rate[mac]['up_kbps'] += stats['up_kbps']
                    avg_rate[mac]['down_kbps'] += stats['down_kbps']

        # Calc average
        for key in ["up_kbps", "down_kbps"]:
            for mac in avg_rate.keys():
                avg_rate[mac][key] = avg_rate[mac][key] / len(self.past_rates)

        return avg_rate

    def run(self):
        prev_summary = None

        all_devices = self.get_device_names()

        while True:
            summary = self.refresh_summary()

            if prev_summary is None:
                prev_summary = summary
                time.sleep(self.sleep_time)
                continue
            else:
                rate = self.calc_diff(prev_summary, summary)

                # Add present rate to past_rates
                self.past_rates.insert(0, rate)
                if len(self.past_rates) > self.bw_avg_window:
                    self.past_rates.pop()

                # Print average stats
                for k, v in self.get_avg_bw_rate().items():
                    # Update Redis
                    try:
                        device_tag = all_devices[k]
                    except KeyError:
                        device_tag = k

                    self.redis.incrbyfloat(device_tag + "_upload", v['up_kbps'])
                    self.redis.incrbyfloat(device_tag + "_download", v['down_kbps'])

                    print device_tag, v

                print

            time.sleep(self.sleep_time)
            prev_summary = summary


if __name__ == "__main__":
    router_monitor = RouterFlow()
    router_monitor.run()
