from rest_framework import serializers
from django.contrib.auth.models import User
from tests.models import Website, Test, UserManager


class TestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Test
        fields = ("pingdom_org", "pingdom_dest",
                  "load_org", "load_dest", "load_redirect",
                   "rtt_org", "rtt_dest", "rtt_redirect")


class WebsiteSerializer(serializers.ModelSerializer):
    site = TestSerializer(many=True)
    user_test = serializers.CharField()

    class Meta:
        model = Website
        depth = 1
        fields = ("id", 
                  "name", "ip_source",
                  "ip_destination", "user_test", 
                  "user_redirect", "redirect","load_data", "redirect_data", "site")
 
    def create(self, validated_data):
        data = validated_data.copy()
        data["user_test"]  = self.context['request'].user
        #print(data["user_test"])
        return super(WebsiteSerializer, self).create(data)


    def update(self, instance, validated_data):
        tests_data = validated_data.pop("site")
        user_test = validated_data.pop("user_test")
        tests = (instance.site).all()
        tests = list(tests)
        instance.name = validated_data.get("name", instance.name)
        instance.user = validated_data.get("user", instance.user)
        instance.load_data = validated_data.get("load_data", instance.load_data)
        instance.redirect_data = validated_data.get("redirect_data", instance.redirect_data)
        print(instance.redirect_data)
        try:
            userid=self.context['request'].user.id
            user_test_obj = UserManager.objects.get(user_id=userid)
            if user_test_obj:
                instance.user_test = user_test_obj
                instance.user_redirect =  user_test_obj
                instance.save()    
        except Exception as e:
            print(e)

        for test_data in tests_data:
            test = tests.pop(0)
            test.load_org = test_data.get("load_org", test.load_org)
            test.load_dest = test_data.get("load_dest", test.load_dest)
            test.load_redirect = test_data.get("load_redirect", test.load_redirect)
            test.rtt_org = test_data.get("rtt_org", test.rtt_org)
            test.rtt_dest = test_data.get("rtt_dest", test.rtt_dest)
            test.rtt_redirect = test_data.get("rtt_redirect", test.rtt_redirect)
            test.save()
        return instance
        #return super().update(instance, user_test_obj)

#    def perform_create(self, serializer):
#        serializer.save(user_test=self.request.user)

