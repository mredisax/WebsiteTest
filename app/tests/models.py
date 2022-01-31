from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django.conf import settings
from django.contrib.auth.models import User
from unidecode import unidecode
from django.db.models import Avg, F
import os


# Create your models here.
def test_path(instance, filename):
    return "test_file/{0}/{1}".format(instance.name, filename)

redirect_choice = [
    ("TAK", "TAK"),
    ("NIE", "NIE"),
]

progress_status = [
    ("Nowe", "Nowe"),
    ("W Trakcie", "W Trakcie"),
    ("Load", "Load"),
    ("Zawieszone", "Zawieszone"),
    ("Zakończone", "Zakończone"),
    ("Wygenerowane", "Wygenerowane"),
    ("Anulowane", "Anulowane"),
]


class UserManager(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField("Imie", blank=True, max_length=100)
    last_name = models.CharField("Nazwisko", blank=True, max_length=100)
    network = models.CharField("Dostawca internetu", max_length=100)
    network_speed = models.CharField("Prędkość[mb/s]", max_length=100)

    class Meta:
        verbose_name = "Ustawienia Użytkownika"
        verbose_name_plural = "Ustawienia Użytkowników"

    def __str__(self):
        return str(self.user)


class Website(models.Model):
    status = models.CharField(
        "Status",
        max_length=100,
        default="Nowe",
        choices=progress_status)
    slug = models.SlugField("Link", max_length=300, blank=True)
    create_data = models.DateTimeField("Data dodania", default=timezone.now)
    load_data = models.DateTimeField("Data przeglądarki", blank=True, default=timezone.now)
    redirect_data = models.DateTimeField("Data przekierowania", blank=True, default=timezone.now)
    end_data = models.DateTimeField("Data zakończenia", auto_now=True)
    name = models.CharField("Nazwa", max_length=200)
    ip_source = models.CharField("IP źródłowe", max_length=60)  # ip_old_server
    ip_destination = models.CharField(
        "IP docelowe", max_length=60)  # ip_new_server
    server_name = models.CharField("Nazwa serwer(opcjonalnie)", max_length=60, blank=True)
    jira = models.CharField(max_length=200)
    old_host_name = models.CharField(
        "Nazwa starego usługodawcy", max_length=60)
    redirect = models.CharField(
        "Przekierowanie",
        max_length=30,
        default="NIE",
        choices=redirect_choice)
    description = models.TextField("Opis i Informacje", default='', blank=True, max_length=3000)
    # file
    pingdom_org_file = models.FileField(
        "pingdom_org", upload_to=test_path, blank=True)
    pingdom_dest_file = models.FileField(
        "pingdom_dest", upload_to=test_path, blank=True)
    load_org_file = models.FileField(
        "load_org", upload_to=test_path, blank=True)
    load_dest_file = models.FileField(
        "load_dest", upload_to=test_path, blank=True)
    load_redirect_file = models.FileField(
        "load_redirect", upload_to=test_path, blank=True)
    rtt_org_file = models.FileField("rtt_org", upload_to=test_path, blank=True)
    rtt_dest_file = models.FileField(
        "rtt_dest", upload_to=test_path, blank=True)
    rtt_redirect_file = models.FileField(
        "rtt_redirect", upload_to=test_path, blank=True)
    user = models.ForeignKey(UserManager, related_name="pingdom_user", on_delete=models.CASCADE, null=True)
    user_test = models.ForeignKey(UserManager, related_name="load_user", blank=True, on_delete=models.CASCADE, null=True)
    user_redirect = models.ForeignKey(UserManager, related_name="redirect_user", blank=True, on_delete=models.CASCADE, null=True)

    pingdom_org_avg = models.IntegerField(blank=True, default=0)
    pingdom_dest_avg = models.IntegerField(blank=True, default=0)
    pingdom_diff = models.IntegerField(blank=True, default=0)
    load_org_avg = models.IntegerField(blank=True, default=0)
    load_dest_avg = models.IntegerField(blank=True, default=0)
    load_redirect_avg = models.IntegerField(blank=True, default=0)
    load_diff = models.IntegerField(blank=True, default=0)
    rtt_org_avg = models.IntegerField(blank=True, default=0)
    rtt_dest_avg = models.IntegerField(blank=True, default=0)
    rtt_redirect = models.IntegerField(blank=True, default=0)
    rtt_redirect_avg = models.IntegerField(blank=True, default=0)
    rtt_diff = models.IntegerField(blank=True, default=0)

    # def get_diff(self):
    #     return Test.objects.filter(site=self).aggregate(
    #         p_sub=Avg("pingdom_dest") - Avg("pingdom_org"),
    #         l_sub=Avg("load_dest") - Avg("load_org"),
    #         rtt_sub=Avg("rtt_dest") - Avg("rtt_org"),
    #         )

    class Meta:
        verbose_name = "Strony"
        verbose_name_plural = "Strony"

    def get_absulute_url(self):
        kwargs = {
            'pk': self.id,
            "slug": self.slug
        }
        return reverse("website_list_view", kwargs=kwargs)

    def save(self, *args, **kwargs):
        value = self.name
        self.slug = slugify(unidecode(value))
    #    if self.status == "Zakończone":
    #        self.end_data = timezone.now
    #    if self.redirect == "TAK" and self.status == "Load":
    #        self.redirect_data = timezone.now
        super(Website, self).save(*args, **kwargs)

    def __str__(self):
        return self.name


class Test(models.Model):
    site = models.ForeignKey(
        Website,
        related_name="site",
        on_delete=models.CASCADE)
    pingdom_org = models.IntegerField(blank=True, default=0)
    pingdom_dest = models.IntegerField(blank=True, default=0)
    load_org = models.IntegerField(blank=True, default=0)
    load_dest = models.IntegerField(blank=True, default=0)
    load_redirect = models.IntegerField(blank=True, default=0)
    rtt_org = models.IntegerField(blank=True, default=0)
    rtt_dest = models.IntegerField(blank=True, default=0)
    rtt_redirect = models.IntegerField(blank=True, default=0)


    
