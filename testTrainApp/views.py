from django.shortcuts import render
from django.contrib.auth.models import User, Group
from rest_framework import viewsets, permissions
from rest_framework.decorators import api_view

from testTrainApp.serializers import UserSerializer, GroupSerializer

from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.parsers import JSONParser

from django.db.models import F
from testTrainApp.models import Train, TrainStop, Station
from testTrainApp.serializers import TrainSerializer, StationsSerializer
from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import LimitOffsetPagination, PageNumberPagination
from .serializers import OwnStationSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer


class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer


class BasicPagination(PageNumberPagination):
    page_size_query_param = 'limit'


class StationViewSet(APIView):
    pagination_class = BasicPagination

    @property
    def paginator(self):
        if not hasattr(self, '_paginator'):
            if self.pagination_class is None:
                self._paginator = None
            else:
                self._paginator = self.pagination_class()
        else:
            pass
        return self._paginator

    def paginate_queryset(self, queryset):

        if self.paginator is None:
            return None
        return self.paginator.paginate_queryset(queryset,
                                                self.request, view=self)

    def get_paginated_response(self, data):
        assert self.paginator is not None
        return self.paginator.get_paginated_response(data)

    def get(self, request, format=None, *args, **kwargs):
        stations = Station.objects.all()
        page = self.paginate_queryset(stations)
        if page is not None:
            serializer = self.get_paginated_response(StationsSerializer(page, many=True).data)
        else:
            serializer = StationsSerializer(stations, many=True)
        return Response(serializer.data)



class StationViewSet2(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = LimitOffsetPagination

    @property
    def paginator(self):
        if not hasattr(self, '_paginator'):
            if self.pagination_class is None:
                self._paginator = None
            else:
                self._paginator = self.pagination_class()
        else:
            pass
        return self._paginator

    def paginate_queryset(self, queryset):

        if self.paginator is None:
            return None
        return self.paginator.paginate_queryset(queryset,
                                                self.request, view=self)

    def get_paginated_response(self, data):
        assert self.paginator is not None
        return self.paginator.get_paginated_response(data)

    def get(self, request, format=None, *args, **kwargs):
        fnd = request.GET.get('fnd')
        stations = Station.objects.filter(name__startswith=fnd)
        result = []
        counter = 0
        for station in stations:
            if counter == 50:
                break
            result.append({"name": station.name, "id": counter})
            counter += 1
        # res_stat = OwnStationSerializer(result, many=True).data
        page = self.paginate_queryset(result)
        if page is not None:
            serializer = self.get_paginated_response(OwnStationSerializer(page, many=True).data)
        else:
            serializer = StationsSerializer(stations, many=True)
        return Response(serializer.data)


def departures_from_the_station(src, time):
    allTrainsFromStation = list(TrainStop.objects.filter(
        station__name=src, departure_time__gte=time).order_by('departure_time'))
    return allTrainsFromStation


def departures_from_the_station_desc(src, time):
    allTrainsFromStation = list(TrainStop.objects.filter(
        station__name=src, departure_time__gte=time).order_by('-departure_time'))
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


def stations_on_the_train_route3(train, time):
    stops = TrainStop.objects.filter(train__number=train.train.number).order_by(
        F('departure_time').desc(nulls_first=True)
    )
    if stops[0].departure_time == None:  # Odstranime stanic ktore su pod zvolenym casom okrem None
        final_stop = list(stops.filter(departure_time=None))
        stops = list(stops.filter(departure_time__gte=time))
        stops = final_stop + stops
    else:
        stops = list(stops.filter(departure_time__gte=time))
    stops = list(stops)
    stops.pop(-1)
    return stops


def stations_on_the_train_route_asc(train, time):
    stops = TrainStop.objects.filter(train__number=train.train.number).order_by(
        F('departure_time').asc(nulls_last=True)
    )
    if stops[len(stops)-1].departure_time == None:  # Odstranime stanic ktore su pod zvolenym casom okrem None
        final_stop = list(stops.filter(departure_time=None))
        stops = list(stops.filter(departure_time__gte=time))
        stops = stops + final_stop
    else:
        stops = list(stops.filter(departure_time__gte=time))

    return stops


def contains_destination(stops, dst):
    """
    funkcia prechacza zoznam vlakovych stanic a hlada ci neobsahuje ciel
    :param stops: zoznam stanic ktorimy vlak prechadza
    :param dst: cielova stanica
    :return: index na ktorej je cielova stanica, inak false
    """
    stop_counter = 0
    for stop in stops:
        if stop.station.name == dst:
            return stop_counter
        stop_counter += 1
    return False


def contains_destination3(stops, dst):
    """
    funkcia prechacza zoznam vlakovych stanic a hlada ci neobsahuje ciel
    :param stops: zoznam stanic ktorimy vlak prechadza
    :param dst: cielova stanica
    :return: index na ktorej je cielova stanica, inak false
    """
    stop_counter = 0
    for stop in stops:
        if stop.station.name == dst:
            return stop_counter
        stop_counter += 1
    return -1


def create_connection_information(train, stops, dest_index):
    """
    funkcia na vytvaranie informacii podla sablony pre pozdejsie parsovanie do JSON-u
    :param train: komplexne informacie o vlaku
    :param stops: komplexne informacie o jeho zastavkach
    :param dest_index: index na ktorom sa vyskytuje cielova zastavka zo vsetkych zastavok
    :return: slovnik (dict) s klucovimi hodnotami
    """
    connection_info = {
        "number": train.train.number,
        "name": train.train.name,
        "src": stops[0].station.name,
        "departure_time": stops[0].departure_time,
        "dst": stops[dest_index].station.name,
        "arrival_time": stops[dest_index].arrival_time,
        "distance": stops[dest_index].distance - stops[0].distance
    }
    return connection_info


def create_connection_information3(train, stops, dest_index):
    """
    funkcia na vytvaranie informacii podla sablony pre pozdejsie parsovanie do JSON-u
    :param train: komplexne informacie o vlaku
    :param stops: komplexne informacie o jeho zastavkach
    :param dest_index: index na ktorom sa vyskytuje cielova zastavka zo vsetkych zastavok
    :return: slovnik (dict) s klucovimi hodnotami
    """
    connection_info = {
        "number": train.train.number,
        "name": train.train.name,
        "src": stops[-1].station.name,
        "departure_time": stops[-1].departure_time,
        "dst": stops[dest_index].station.name,
        "arrival_time": stops[dest_index].arrival_time,
        "distance": stops[dest_index].distance - stops[-1].distance
    }
    return connection_info


def search_for_connections2(actual_transfer, max_transfer, src, dst, time):
    """
    funkcia vracia zoznam spojov podla zadanych poziadaviek
    :param actual_transfer: aktualny prestup
    :param max_transfer: maximalny pocet prestupov
    :param src: vychodzia stanica
    :param dst: cielova stanica
    :param time: minimalny cas
    :return: zoznam spojov
    """
    trains_list = []
    new_added = False
    trains_from_station = departures_from_the_station(src, time)
    for train in trains_from_station:
        stops = stations_on_the_train_route_asc(train, train.departure_time)
        dest_index = contains_destination(stops, dst)
        for transfer in range(actual_transfer, max_transfer+1):
            if new_added:
                new_added = False
                break


            if transfer == 0:
                if dest_index:
                    result = [create_connection_information(train, stops, dest_index)]
                    trains_list.append(result)
                    break
                else:
                    stops_list = list(stops)
                    stops_list.pop(0)
                    for stop in reversed(stops_list):
                        time = stop.departure_time
                        if time is None:
                            time = stop.arrival_time
                        result = [create_connection_information(train, stops, len(stops_list))]
                        result.append(search_for_connections2(transfer+1, max_transfer, stop.station.name, dst, time))
                        if len(result[-1]) != 0:
                            trains_list.append(result)
                            new_added = True
                            break
            elif transfer == 1:
                info = []
                if dest_index:
                    return create_connection_information(train, stops, dest_index)
                else:
                    stops_list = list(stops)
                    stops_list.pop(0)
                    for stop in reversed(stops_list):
                        time = stop.departure_time
                        if time is None:
                            time = stop.arrival_time

                        result = [create_connection_information(train, stops, len(stops_list))]
                        result.append(search_for_connections2(transfer + 1, max_transfer, stop.station.name, dst, time))
                        if len(result[-1]) != 0:
                            trains_list.append(result)
                            new_added = True
                            break
            elif transfer == 2:
                info = []
                if dest_index:
                    return create_connection_information(train, stops, dest_index)


    return trains_list







def search_for_connections(transfer, src, dst, time, result):
    trains_from_station = departures_from_the_station(src, time)

    trainslist = []
    for train in trains_from_station:
        time = train.arrival_time
        if time is None:
            time = train.departure_time
        stops = stations_on_the_train_route(train, time)
        #print(stops)
        # je niektora zo zastavok cielova

        if transfer == 2:
            result = []
            return result
        else:
            for stop in stops:
                if len(result) > 0 and result[-1]['number'] == train.train.number:  # jedna sa o ten isty vlak prichod a hned odchod
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
                    break
                    #return trainslist

                else:
                    result.append({
                        "number": train.train.number,
                        "name": train.train.name,
                        "src": src,
                        "dst": stop.station.name
                    })
                    time = stop.departure_time
                    if time is None:
                        time = stop.arrival_time
                    connect = search_for_connections(transfer + 1, stop.station.name, dst, stop.arrival_time, result)
                    if len(connect) != 0:
                        if isinstance(trainslist, list):
                            trainslist += connect
                        else:
                            trainslist.append(connect)
                    if not bool(result[-1]):  # kontroluje ci je posledny pridany prazny a teda sa nenasla dalsia cesta
                        #del result[-(transfer+2):]
                        result.pop()
                        result.pop()

                    else:
                        result = []
                    '''
            result.append(trainslist)
            '''
    if len(trains_from_station) == 0 or trains_from_station[-1].train.number == train.train.number:
        result.append({})
    return trainslist


def search_for_connections3(transfer, src, dst, time, result):
    trains_list = []
    if transfer == 2:
        return trains_list
    trains_from_station = departures_from_the_station_desc(src, time)
    if not trains_from_station:
        return []
    for train in trains_from_station:
        if len(result) > 0 and result[-1]['number'] == train.train.number:  # jedna sa o ten isty vlak prichod a hned odchod
            continue
        time = train.arrival_time
        if time is None:
            time = train.departure_time
        stops = stations_on_the_train_route3(train, time)
        print(stops)
        dest_index = contains_destination3(stops, dst)
        if dest_index >= 0:
            result = [create_connection_information3(train, stops, dest_index)]
            trains_list.append(result)
            continue
        else:
            dst_index = 0
            for stop in stops:
                result = [create_connection_information3(train, stops, dst_index)]
                connect = search_for_connections3(transfer + 1, stop.station.name, dst, stop.arrival_time, result)
                dst_index += 1
                if not connect:
                    continue
        print(trains_list)



    return trains_list


class TrainResultList(APIView):
    def get(self, request, format=None):
        time = self.request.query_params.get('time')
        src = request.GET.get('src')
        dst = request.GET.get('dst')
        result = []
        #result = search_for_connections(0, src, dst, time, result)
        #trains_list = search_for_connections3(0, src, dst, time, result)
        result = search_for_connections2(0, 1, src, dst, time)
        return Response(result)
        #return Response(trains_list)


class TrainInfo(APIView):
    def get(self, request, format=None):
        train_number = self.request.query_params.get('train')
        stops = TrainStop.objects.filter(train__number=train_number).order_by(
            F('departure_time').asc(nulls_last=True)
        )
        print(stops)
        route = []
        for stop in stops:
            route.append({
                "station": stop.station.name,
                "arrival_time": stop.arrival_time,
                "departure_time:": stop.departure_time,
                "distance": stop.distance
            })
        name = Train.objects.get(number=train_number)
        info = {"name": name.name, "route": route}
        return Response(info)


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
