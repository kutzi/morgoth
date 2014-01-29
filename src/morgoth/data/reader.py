
from datetime import datetime, timedelta
from mongo_clients import MongoClients
from morgoth.data import get_col_for_metric
from morgoth.utc import utc
import re

class Reader(object):
    def __init__(self):
        self._db = MongoClients.Normal.morgoth

    def get_metrics(self, pattern=None):
        metrics = []
        for metric in self._db.meta.find():
            name = metric['_id']
            if pattern and not re.match(pattern, name):
                continue
            metrics.append(name)
        return metrics

    def get_data(self, metric, start=None, stop=None, step=None):
        time_query = {}
        if start:
            time_query['$gte'] = start
        if stop:
            time_query['$lte'] = stop
        col = get_col_for_metric(self._db, metric)
        query = {'metric' : metric}
        if time_query:
            query['time'] = time_query
        data = col.find(query)
        time_data = []

        count = 0
        total = 0.0
        boundary = None
        if start and step:
            boundary = (start + step).replace(tzinfo=utc)
        for point in data:
            if boundary and step:
                if point['time'] > boundary:
                    if count > 0:
                        time_data.append((boundary.isoformat(), total / count))
                    boundary += step
                    count = 0
                    total = 0.0
                count += 1
                total += point['value']

            else:
                time_data.append((point['time'].isoformat(), point['value']))
        if count > 0:
            time_data.append((boundary.isoformat(), total / count))
        return time_data

