import json
import http.client
from datetime import datetime

api_key = None
node = None

class ProcessEventsResponse:
    def __init__(self, ok=True, data=''):
        self.ok = ok
        self.data = data


class GetInventory():
    def do(room_type_id):
        headers = {
            'accept': "application/json",
            'content-type': "application/json",
            'authorization': f"Bearer {api_key}"
        }

        conn = http.client.HTTPSConnection(f"{node}.tendzin.com")

        start_day = datetime.today().replace(day=1).strftime('%Y-%m-%d')

        conn.request(
            "GET",
            f"/range/day/{room_type_id}/inventories?upper-range-gte={start_day}",
            None,
            headers)

        res = conn.getresponse()

        data = res.read()

        result = json.loads(data)['result']

        return list(map(lambda x: {
            'count': x['count'],
            'total': x['total'],
            'range_lower': x['range']['lower'],
            'range_upper': x['range']['upper'],
        }, result))


class UpdateInventory():
    def do(room_type_id, total, range_lower, range_upper):
        headers = {
            'accept': "application/json",
            'content-type': "application/json",
            'authorization': f"Bearer {api_key}"
        }

        payload = json.dumps({
            'events': [
                {
                    'operation': "flatten",
                    'column': "total",
                    'delta': total,
                    'range': {
                        'lower': range_lower,
                        'upper': range_upper,
                    },
                }
            ]
        })

        conn = http.client.HTTPSConnection(f"{node}.tendzin.com")

        conn.request("PATCH", f"/range/day/{room_type_id}", payload, headers)

        res = conn.getresponse()

        if res.status != 204:
            return ProcessEventsResponse(False, json.loads(res.read()))
        return ProcessEventsResponse()


class MakeReservation():
    def do(reservation_id, room_type_id, check_in, last_night):
        transaction_id = reservation_id

        headers = {
            'accept': "application/json",
            'content-type': "application/json",
            'tendzin-transaction-id': f"{transaction_id}",
            'authorization': f"Bearer {api_key}"
        }

        print(headers)
        payload = json.dumps({
            'events': [
                {
                    'operation': "increment",
                    'column': "count",
                    'delta': 1,
                    'range': {
                        'lower': check_in.strftime('%Y-%m-%d'),
                        'upper': last_night.strftime('%Y-%m-%d'),
                    },
                }
            ]
        })

        conn = http.client.HTTPSConnection(f"{node}.tendzin.com")

        conn.request("PATCH", f"/range/day/{room_type_id}", payload, headers)

        res = conn.getresponse()

        if res.status != 204:
            return ProcessEventsResponse(False, json.loads(res.read()))
        return ProcessEventsResponse()


class CancelReservation():
    def do(reservation_id, room_type_id, check_in, last_night):

        headers = {
            'accept': "application/json",
            'content-type': "application/json",
            'authorization': f"Bearer {api_key}"
        }

        payload = json.dumps({
            'events': [
                {
                    'operation': "decrement",
                    'column': "count",
                    'delta': 1,
                    'range': {
                        'lower': check_in.strftime('%Y-%m-%d'),
                        'upper': last_night.strftime('%Y-%m-%d'),
                    },
                }
            ]
        })

        conn = http.client.HTTPSConnection(f"{node}.tendzin.com")

        conn.request("PATCH", f"/range/day/{room_type_id}", payload, headers)

        res = conn.getresponse()

        if res.status != 204:
            return ProcessEventsResponse(False, json.loads(res.read()))
        return ProcessEventsResponse()
