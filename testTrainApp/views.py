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
    stops = TrainStop.objects.filter(train__number=train.train.number).order_by(
        F('departure_time').desc(nulls_first=True)
    )
    if stops[0].departure_time == None:  # Odstranime stanic ktore su pod zvolenym casom okrem None
        final_stop = list(stops.filter(departure_time=None))
        stops = list(stops.filter(departure_time__gte=time))
        stops = final_stop + stops
    else:
        stops = list(stops.filter(departure_time__gte=time))

    return stops


def search_for_connections(transfer, src, dst, time, result):
    trains_from_station = departures_from_the_station(src, time)

    trainslist = []
    for train in trains_from_station:
        time = train.arrival_time
        stops = stations_on_the_train_route(train, time)
        print(stops)
        # je niektora zo zastavok cielova

        if transfer == 5:
            return result
        else:
            for stop in stops:
                if len(result) > 0 and result[-1]['number'] == train.train.number:
                    continue
                if stop.station.name == src:  # vychodzie stanice sa zhoduju
                    continue
                if stop.station.name == dst:
                    result.append({
                        "number": train.train.number,
                        "name": train.train.name,
                        "src": src,
                        "dst": dst

                    })
                    #'''

                    trainslist.append(result)
                    result = []
                    return trainslist

                else:
                    result.append({
                        "number": train.train.number,
                        "name": train.train.name,
                        "src": src,
                        "dst": stop.station.name
                    })
                    connect = search_for_connections(transfer + 1, stop.station.name, dst, stop.arrival_time, result)
                    if len(connect) != 0:
                        #'''
                        if isinstance(trainslist, list):
                            trainslist += connect
                        else:
                            trainslist.append(connect)  # ak je list tak len spoj
                        #'''
                        #trainslist.append(connect)
                    if not bool(result[-1]):
                        #del result[-(transfer+2):]
                        result.pop()
                        result.pop()

                    #elif result[-1]['dst'] == dst:
                     #   trainslist.append(result)
                     #   result = []

                    else:
                        result = []
                    '''
            result.append(trainslist)
            '''
    if len(trains_from_station) == 0 or trains_from_station[-1].train.number == train.train.number:
        result.append({})
    return trainslist


class TrainResultList(APIView):
    def get(self, request, format=None):
        time = self.request.query_params.get('time')
        src = request.GET.get('src')
        dst = request.GET.get('dst')
        result = []
        result = search_for_connections(0, src, dst, time, result)
        '''
        transfer = 0
        max_transfer = 5

        result = []

        # zoznam vlakov odchadzajucich zo stanice v pozadovanom case
        allTrainsFromStation = departures_from_the_station(src, time)
        print(allTrainsFromStation)
        # zoznam stanic ktore konkretny vlak navstivi
        for train in allTrainsFromStation:
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
        '''
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
