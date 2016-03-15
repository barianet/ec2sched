from docopt import docopt
from ConfigParser import SafeConfigParser
from boto3.session import Session
import json
import time

config = SafeConfigParser()


def run(args):

    config.read([args['--config'], 'aws.conf'])
    init()
    schedule()

    # Cron or...
    # while True:
    #    schedule()
    #    time.sleep(3600)


def init():

    aws_access_key = config.get('aws_us', 'access_key', '')
    aws_secret_key = config.get('aws_us', 'secret_key', '')
    aws_region = config.get('aws_us', 'region', '')

    s = Session(
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=aws_region,
            )

    global ec2
    ec2 = s.resource('ec2')
    global schedules
    schedules = get_schedules()


def get_schedules():
    path = config.get('schedule', 'paths', './schedule.json')
    with open(path) as schedule_file:
        return json.load(schedule_file)


def schedule():
    for profile in schedules['profiles']:
        instances = _get_instances(profile['instance_tags'])
        start_stop_instances(instances, profile['schedule'])


def _get_instances(instance_tags):
    return ec2.instances.filter(Filters=[{'Name': 'tag:Name', 'Values': instance_tags}])


def start_stop_instances(instances, ec2schedule):
    for instance in instances:
        if instance.state['Name'] == 'running' and _get_desired_state(ec2schedule) == 'stop':
            print "Should stop " + instance.id + "."
            instance.stop()
        elif instance.state['Name'] == 'stopped' and _get_desired_state(ec2schedule) == 'start':
            print "Should start " + instance.id + "."
            instance.start()
        else:
            print "Nothing to do."


def _get_desired_state(schedule):

    print "_get_desired_state called"
    current_hour = int(time.strftime("%H", time.localtime()))
    current_week_day = time.strftime("%A", time.localtime()).lower()
    start = schedule[current_week_day]['start']
    stop = schedule[current_week_day]['stop']

    state = 'stop'
    if start <= current_hour < stop:
        state = 'start'

    print state
    return state


def _get_instance_ids(instances):

    instance_ids = []
    for instance in instances:
        instance_ids.append(instance.id)

    return instance_ids


if __name__ == "__main__":
    args = docopt(__doc__, version='scheduler 1.0')
    run(args)