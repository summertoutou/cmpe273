import subprocess

ip_list = ['52.8.191.254','52.54.63.252','52.16.0.2','50.112.120.53','52.58.63.252','52.56.34.0','52.222.9.163',
           '52.60.50.0','52.15.55.0','52.68.63.252','52.78.63.252','52.76.0.2','52.64.63.253','52.66.66.2','54.94.0.66']
region_list = ['us-west-1','us-east-1','eu-west-1','us-west-2','eu-central-1','eu-west-2','us-gov-west-1',
               'ca-central-1','us-east-2','ap-northeast-1','ap-northeast-2','ap-southeast-1','ap-southeast-2',
               'ap-south-1','sa-east-1']
dict = {}
result = []
for i in range(15):
    ping = subprocess.Popen(
        ["ping", "-c", "3", ip_list[i]],
        stdout = subprocess.PIPE,
        stderr = subprocess.PIPE
    )

    out, error = ping.communicate()
    lines = out.splitlines()
    z=len(lines)
    time = float(lines[7].split("/")[4])
    r_time = format(time, '.3f')
    dict[r_time] = region_list[i]+" ["+ip_list[i]+"]"
    result.append(r_time)

result.sort(key=float)


for i in range(15):
    str_i = str(i+1) + ". " + dict[result[i]] + " - " + result[i]
    print str_i


