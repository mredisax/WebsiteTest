from django.shortcuts import render
from tests.models import Website, Test, UserManager
from django.db.models import Avg
from tests.tasks import pingdom_selenium_test, cron_check_ip, check_end_of_test
from app.celery import app
from celery_once import AlreadyQueued
from django.contrib.auth.decorators import login_required
from celery.result import AsyncResult
from django.http import HttpResponse
from django.http.response import JsonResponse
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from tests.serializers import WebsiteSerializer
from django.views.generic import ListView
from django.db.models import Q
import json


@login_required(login_url='/admin')
def homepage_view(request):
    websites = Website.objects.all().order_by("create_data")
    context = {
        "websites": websites
    }
    return render(request, "index.html", context)

@login_required(login_url='/admin')
def website_view(request, slug, id):
    query_pk_and_slug = True
    website = Website.objects.get(id=id, slug=slug)
    test = Test.objects.filter(site_id=id).order_by("-id")
    avg = test.aggregate(p_org=Avg("pingdom_org"),
                         p_dest=Avg("pingdom_dest"), l_org=Avg("load_org"),
                         l_dest=Avg("load_dest"), l_red=Avg("load_redirect"),
                         o_rtt=Avg("rtt_org"), d_rtt=Avg("rtt_dest"),
                         r_red=Avg("rtt_redirect"))
#    website_get_avg(website, avg)
    try:
        pingdom_selenium_test.apply_async(
            args=[id, slug, website, test], task_id=id) #, task_id=id
    except AlreadyQueued:
        print("Task w trakcie wykonywania")

    context = {
        "website": website,
        "test": test,
        "avg": avg.values(),
        "task_id": id,
    }
    return render(request, "website.html", context)

#def website_get_avg(website, avg):
#    try:
#        website.pingdom_org_avg = int(avg["p_org"]) 
#        website.pingdom_dest_avg = int(avg["p_dest"])
#        website.load_org_avg = int(avg["l_org"])
#        website.load_dest_avg = int(avg["l_dest"])
#        website.load_redirect_avg = int(avg["l_red"])
#        website.rtt_org_avg = int(avg["o_rtt"])
#        website.rtt_dest_avg = int(avg["d_rtt"])
#        website.rtt_redirect = int(avg["r_red"])
#        
#        website.pingdom_diff = int(avg["p_dest"]) - int(avg["p_org"])
#        website.load_diff = int(avg["l_dest"]) - int(avg["l_org"])
#        website.rtt_diff = int(avg["d_rtt"]) - int(avg["o_rtt"])
#        website.save()
#    except Exception as e:
#        print(e)

# DRF
@api_view(['GET'])
@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
def website_view_api(request):
    try:
        websites = Website.objects.all().filter(Q(status="W Trakcie") | Q(status="Load"))
    except Website.DoesNotExist:
        return JsonResponse(
            {'message': 'The website does not exist'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        website_serializer = WebsiteSerializer(websites, many=True)
        return Response(website_serializer.data)


@api_view(['GET', 'PUT', 'POST'])
@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
def website_update_api(request, id):
    try:
        websites = Website.objects.get(id=id)
    except Website.DoesNotExist:
        return JsonResponse(
            {'message': 'The website does not exist'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        website_serializer = WebsiteSerializer(websites)
        return JsonResponse(website_serializer.data)

    elif request.method == 'PUT' or request.method == "POST":
        website_data = JSONParser().parse(request)
        #user_test_temp = UserManager.objects.get(id=request.user.id) 
        #website_data["user_test"] = user_test_temp
        print(website_data)
        website_serializer = WebsiteSerializer(websites, data=website_data, context={'request': request}) 
        if website_serializer.is_valid():
            website_serializer.save()
            return JsonResponse(website_serializer.data)
        return JsonResponse(
            website_serializer.errors,
            status=status.HTTP_400_BAD_REQUEST)


# Generate report
@login_required(login_url='/admin')
def website_report_view(request):
    websites = Website.objects.filter(status="Zakończone")
    context = {
        "websites": websites,
    }
    return render(request, "generate.html", context)

