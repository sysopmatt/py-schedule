import praw
import time
import csv
import os

from .models import Schedule
from celery import shared_task, app, task
from tvdb_api_client import TVDBClient
from datetime import datetime, timedelta
from celery.schedules import crontab


@app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(
        crontab(minute=1),
        test.s("world")
    )
    sender.add_periodic_task(
        crontab(minute=1),
        sample_task()
    )


@shared_task
def test(arg):
    print(arg)


@shared_task
def add(x, y):
    return x + y


@shared_task
def mul(x, y):
    return x * y


@shared_task
def xsum(numbers):
    return sum(numbers)


@shared_task
def count_widgets():
    return Schedule.objects.count()


@shared_task
def rename_widget(widget_id, name):
    w = Schedule.objects.get(id=widget_id)
    w.name = name
    w.save()


@shared_task
def post_to_reddit(title, body, show):
    # Post to Reddit
    reddit = praw.Reddit('bot1')
    reddit.validate_on_submit = True
    sub = reddit.subreddit(os.environ.get('SUBREDDIT-' + show))
    footer_file = show + '-footer.txt'
    if os.path.exists(footer_file):
        with open(footer_file, 'r') as file:
            footer = file.read()
    else:
        footer = '\n\n'
    post = sub.submit({title}, selftext=body + footer, send_replies=False)
    time.sleep(1)
    reddit.submission(id=post.id).mod.distinguish(how="yes")
    # reddit.submission(id=post.id).mod.flair(text="episode discussion", css_class="bot")
    reddit.submission(id=post.id).mod.sticky()


@shared_task
def get_episode_info(posttype, todaydate, tvdb_id, show):
    client = TVDBClient(os.environ.get('THETVDB_USERNAME'),
                        os.environ.get('THETVDB_USERKEY'),
                        os.environ.get('THETVDB_APIKEY'))
    episodes = client.get_episodes_by_series(tvdb_id)
    t, b, d = [], [], []
    for episode in episodes:
        if episode['firstAired'] != '':
            epdt = datetime.strptime(episode['firstAired'], '%Y-%m-%d').date()
            offset = int(os.environ.get('TIME_OFFSET')) if int(os.environ.get('TIME_OFFSET')) > 0 else 0
            if todaydate.date() <= epdt < datetime.today().date() + timedelta(
                    days=1) + timedelta(hours=offset):  # Make sure date is not future
                synopsis = '*' + episode['overview'] + '*' if episode['overview'] is not None else ''
                d.append(epdt)
                t.append(show + ' - Season ' + str(episode['airedSeason']) + ' Episode ' +
                         str(episode['airedEpisodeNumber']) + f' - {posttype} Episode Discussion')
                b.append('''# Season ''' + str(episode['airedSeason']) + ''' Episode ''' +
                         str(episode['airedEpisodeNumber']) + ''' - ''' + episode['episodeName'] + ''''

''' + synopsis + '''\n\n
-------------------------------------------------------------------------------------------------------\n\n''')
    print('Episode information retrieved:\n', t[0])
    return t, b, d


@shared_task
def generate_post(title, body):
    eps = (len(title) + len(body)) / 2
    #  post_to_reddit(title, body)
    if eps > 1:
        #  Create multi thread
        megabody, megatitle, eps = '', '', ''
        for synopsis in body:
            megabody = megabody + synopsis
        for ep in title:
            eps = eps + str(ep.split(' ')[5]) + ', '
        eps = eps[0:len(eps) - 2]
        megatitle = title[0].replace(str(title[0].split(' ')[5]), eps)  # Need to fix this for shows with a number
        return megatitle, megabody
    else:
        return title[0], body[0]


def evaluate_schedules(dt):
    with open('schedule.csv', newline='') as csvschedule:
        schedule = csv.DictReader(csvschedule, delimiter=',')
        for row in schedule:
            if dt.hour == int(row['hour']) and dt.minute == int(row['minute']):
                return row['thread'], False, row['show'], row['tvdb_id']
            if row['thread'] == 'Test':  # testing
                return row['thread'], False, row['show'], row['tvdb_id']
    return '', True, '', ''


def get_time():
    t = datetime.now() + timedelta(hours=float(os.environ.get('TIME_OFFSET')))
    return t


@shared_task
def init():
    thread, tvdb_id, sub = '', '', ''
    loop = True
    d = get_time()
    print('Evaluating the schedule...  Current time is: ' + str(d))
    while loop:  # Check to see if it's time to post the episode
        d = get_time()
        thread, loop, show, tvdb_id = evaluate_schedules(d)
        time.sleep(1)

    #  Get episode information
    print('Scheduled post found for the sub /r/' + os.environ.get('SUBREDDIT-' + show) + ' for '
          + show + ' for the "' + thread + '" discussion thread.')
    tlst, blst, dlst = get_episode_info(thread, d, tvdb_id, show)
    try:
        datefromlist = str(dlst[0])
    except IndexError:
        print("No episode airs today")
    else:
        datefromd = str(d.date())
        if datefromlist == datefromd:  # Create the post (handles mega threads)
            t, b = generate_post(tlst, blst)
            #  Post to reddit
            post_to_reddit(t, b, show)
            print('Posting completed!')
    finally:
        print('Exiting loop.  Sleeping for 60 seconds before re-check.')
        time.sleep(60)


@shared_task
def sample_task():
    print("The sample task just ran.")
