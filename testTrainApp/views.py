from django.shortcuts import render
from django.contrib.auth.models import User, Group
from rest_framework import viewsets
from rest_framework.decorators import api_view

from testTrainApp.serializers import UserSerializer, GroupSerializer

from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.parsers import JSONParser

from django.db.models import F
from testTrainApp.models import Train, TrainStop, Station
from testTrainApp.serializers import TrainSerializer
from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer


class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer


def departures_from_the_station(src, time):
    allTrainsFromStation = list(TrainStop.objects.filter(
        station__name=src, departure_time__gte=time).order_by('departure_time'))
    return allTrainsFromStation


def stations_on_the_train_route(train, time):
    #print(time + ">>>>>>>" + time)
    # , departure_time__gte=time
    stops = TrainStop.objects.filter(train__number=train.train.number).order_by(
        F('departure_time').desc(nulls_first=True)
    )
    if stops[0].departure_time == None:  # Odstranime stanic ktore su pod zvolenym casom okrem None
        #print(">>>>>>> "+str(stops.filter(departure_time=None)))
        final_stop = list(stops.filter(departure_time=None))
        stops = list(stops.filter(departure_time__gte=time))
        print("----"+str(final_stop))
        print("----"+str(stops))
        stops = final_stop + stops
        print("++++" + str(stops))
        #stops.insert(0, list(final_stop))
    else:
        stops = list(stops.filter(departure_time__gte=time))

    ''' mozno bude treba dorobit aby nevracalo spoje po hladanom case
    
    for stop in stops:
        if stop.departure_time == None or stop.departure_time 
    '''
    return stops


class TrainResultList(APIView):
    def get(self, request, format=None):
        time = self.request.query_params.get('time')
        src = request.GET.get('src')
        dst = request.GET.get('dst')

        transfer = 0
        max_transfer = 5

        result = []
        '''
        queryset = list(TrainStop.objects.filter(train__number=810).order_by('departure_time'))

        if queryset[0].departure_time == None:
            temp = queryset.pop(0)
            queryset.append(temp)
        print(queryset[0])
        print(queryset)
        print(time + " " + src + " " + dst)
        '''
        # zoznam vlakov odchadzajucich zo stanice v pozadovanom case
        allTrainsFromStation = departures_from_the_station(src, time)
        print(allTrainsFromStation)
        # zoznam stanic ktore konkretny vlak navstivi
        for train in allTrainsFromStation:
            print(train.train.number)
            stops = stations_on_the_train_route(train, time)
            print(stops)
            # je niektora zo zastavok cielova
            trainslist = []
            for stop in stops:
                if stop.station.name == dst:
                    print("mame ciel: "+dst)
                    traininfo = {
                        "number": train.train.number,
                        "name": train.train.name,
                        "src": src,
                        "dst": dst

                    }
                    trainslist.append(traininfo)
                    break
            if len(trainslist) != 0:
                result.append(trainslist)

        return Response(result)


class TrainList(APIView):
    """
    List all trains, or create a new train.
    """

    def get(self, request, format=None):
        trains = Train.objects.all()
        serializer = TrainSerializer(trains, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = TrainSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TrainDetail(APIView):
    """
    retrieve, update or delete a code snippet.
    """

    def get_object(self, number):
        try:
            return Train.objects.get(number=number)
        except Train.DoesNotExist:
            raise Http404

    def get(self, request, number, format=None):
        train = self.get_object(number)
        serializer = TrainSerializer(train)
        return Response(serializer.data)

    def put(self, request, number, format=None):
        train = self.get_object(number)
        serializer = TrainSerializer(train, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, number, format=None):
        train = self.get_object(number)
        train.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
