from celery import Celery
from celery.decorators import task
from .pingdom import Pingdom
from .models import Website, Test
from django.db.models import Avg
from celery_once import QueueOnce
from celery.schedules import crontab
from celery.result import AsyncResult
from celery_once import AlreadyQueued
from django.utils import timezone
import time
import threading
import dns.resolver



@task(serializer="pickle", base=QueueOnce, acks_late=True, time_limit=1800)
def pingdom_selenium_test(id, slug, website, test):
    check_ip(id, slug, website)
    pingdomtype = check_redirect(website)
    timestr = time.strftime("%Y%m%d")
    replace_name = replace_slash(url=website.name)
    path_save_file = f"test_file/{replace_name}/{replace_name}_{pingdomtype}.zip"
    
    if website.status == "Nowe" or website.status == "W Trakcie":
        pingdom_test = Pingdom(
            page_url=website.name,
            pingdomtype=pingdomtype)
        if pingdomtype == "dest":
            if not test:
                print(f"start pingdom2_{pingdomtype} for {website.name}")
                pingdom_result = pingdom_test.pingdom_site()
                for r in pingdom_result:
                    new_test = Test.objects.create(site_id=id, pingdom_dest=r)
                    new_test.save()
                Website.objects.filter(id=id, slug=slug).update(
                    pingdom_dest_file=path_save_file, status="Load")
            elif test[0].pingdom_dest == 0:
                print(f"start pingdom4_{pingdomtype} for {website.name}") 
                id_test = [int(i.id) for i in test]
                pingdom_result = pingdom_test.pingdom_site()
                for r in range(0, len(pingdom_result)):
                    Test.objects.filter(
                        site_id=id, id=id_test[int(r)]).update(
                        pingdom_dest=pingdom_result[int(r)])
                Website.objects.filter(id=id, slug=slug).update(
                    pingdom_dest_file=path_save_file, status="Load") 

        elif pingdomtype == "org":
            if not test:
                print(f"start pingdom1_{pingdomtype} for {website.name}")
                pingdom_result = pingdom_test.pingdom_site()
                for r in pingdom_result:
                    new_test = Test.objects.create(site_id=id, pingdom_org=r)
                    new_test.save()
                Website.objects.filter(id=id, slug=slug).update(
                    pingdom_org_file=path_save_file, status="W Trakcie")
            elif test[0].pingdom_org == 0 or test == None:
                print(f"start pingdom3_{pingdomtype} for {website.name}")
                pingdom_result = pingdom_test.pingdom_site()
                id_test = [int(i.id) for i in test]
                for r in pingdom_result:
                    Test.objects.filter(
                        site_id=id, id=id_test[int(r)]).update(
                        pingdom_dest=pingdom_result[int(r)])
                Website.objects.filter(id=id, slug=slug).update(
                    pingdom_org_file=path_save_file, status="W Trakcie")
    
    else:
        print(f"test pingdom_{pingdomtype} już istnieje")


def replace_slash(url):
    if "/" in url:
        website_name = url.replace("/", "-")
        return website_name 
    else:
        return url

def check_redirect(website):
    if str(website.redirect) == "TAK":
        return "dest"
    else:
        return "org"

def check_ip(id, slug, website):
    site = Website.objects.filter(id=id, slug=slug)
    if "/" in website.name:
        website_name = website.name.split("/")
        website_name = website_name[0]
    else:
        website_name = website.name
    try:
        for rdata in dns.resolver.resolve(website_name, "A"):
            if str(rdata) == str(website.ip_destination):
                print(f"Domena {website_name} przekierowana")
                return site.update(redirect="TAK")
            else:
                print(f"Domena {website_name} nieprzekierowana")
                return site.update(redirect="NIE")
    except dns.resolver.NoNameservers:
        print("Brak rekordu A")

#dns.resolver.NoAnswer
@task()
def cron_check_ip():
    print("Uruchomiono cron_check_ip")
    site = Website.objects.all()
    for i in site:
        if (i.status == "Nowe") or (i.status == "W Trakcie"):
            print(i.name)
            check_ip(id=i.id, slug=i.slug, website=i)

@task()
def cron_pingdom_test():
    site = Website.objects.all()
    for i in site:
        if (i.status == "Nowe") or (i.status == "W Trakcie"):
            test = Test.objects.filter(site_id=i.id)
            print("Uruchomiono cron_pingdom")
            try:
                pingdom_selenium_test.apply_async(args=[i.id, i.slug, i, test])
            except AlreadyQueued:
                print("Task zakolejowany")


def website_get_avg(website, avg):
    try:
        website.pingdom_org_avg = int(avg["p_org"])
        website.pingdom_dest_avg = int(avg["p_dest"])
        website.load_org_avg = int(avg["l_org"])
        website.load_dest_avg = int(avg["l_dest"])
        website.load_redirect_avg = int(avg["l_red"])
        website.rtt_org_avg = int(avg["o_rtt"])
        website.rtt_dest_avg = int(avg["d_rtt"])
        website.rtt_redirect = int(avg["r_red"])
        website.save()
    except Exception as e:
        print(e)

@task()
def check_end_of_test():
    site = Website.objects.all()
    for s in site:
        if s.status == "Load":
            tests = Test.objects.filter(site_id=s.id)
            for t in tests:
                if t.pingdom_org > 0 and t.pingdom_dest > 0 and t.pingdom_org > 0 and t.load_dest > 0 and t.load_redirect > 0 and t.rtt_redirect > 0 and t.rtt_org > 0 and t.rtt_dest > 0:
                    avg = tests.aggregate(p_org=Avg("pingdom_org"),
                         p_dest=Avg("pingdom_dest"), l_org=Avg("load_org"),
                         l_dest=Avg("load_dest"), l_red=Avg("load_redirect"),
                         o_rtt=Avg("rtt_org"), d_rtt=Avg("rtt_dest"),
                         r_red=Avg("rtt_redirect"))
                    website_get_avg(s, avg)

                    Website.objects.filter(id=s.id, slug=s.slug).update(status="Zakończone", end_data=timezone.now())
