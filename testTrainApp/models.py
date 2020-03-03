from django.db import models

# Create your models here.


class Station(models.Model):
    name = models.CharField(max_length=128)

    def __str__(self):
        return self.name


class Train(models.Model):
    number = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=128)
    stops = models.ManyToManyField(Station, through='TrainStop')

    def __str__(self):
        return self.name


class TrainStop(models.Model):
    train = models.ForeignKey(Train, on_delete=models.CASCADE)
    station = models.ForeignKey(Station, on_delete=models.CASCADE)
    arrival_time = models.TimeField(null=True, blank=True)
    departure_time = models.TimeField(null=True, blank=True)

    def __str__(self):
        result = str(self.station) + "-" + str(self.train) + " " + str(self.arrival_time)[:-3] + " | " + str(self.departure_time)[:-3]
        return result

