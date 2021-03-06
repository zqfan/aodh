#
# Copyright 2012 New Dream Network, LLC (DreamHost)
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
"""Base classes for storage engines
"""
import copy
import inspect

import six

import aodh


def dict_to_keyval(value, key_base=None):
    """Expand a given dict to its corresponding key-value pairs.

    Generated keys are fully qualified, delimited using dot notation.
    ie. key = 'key.child_key.grandchild_key[0]'
    """
    val_iter, key_func = None, None
    if isinstance(value, dict):
        val_iter = six.iteritems(value)
        key_func = lambda k: key_base + '.' + k if key_base else k
    elif isinstance(value, (tuple, list)):
        val_iter = enumerate(value)
        key_func = lambda k: key_base + '[%d]' % k

    if val_iter:
        for k, v in val_iter:
            key_gen = key_func(k)
            if isinstance(v, dict) or isinstance(v, (tuple, list)):
                for key_gen, v in dict_to_keyval(v, key_gen):
                    yield key_gen, v
            else:
                yield key_gen, v


def update_nested(original_dict, updates):
    """Updates the leaf nodes in a nest dict.

     Updates occur without replacing entire sub-dicts.
    """
    dict_to_update = copy.deepcopy(original_dict)
    for key, value in six.iteritems(updates):
        if isinstance(value, dict):
            sub_dict = update_nested(dict_to_update.get(key, {}), value)
            dict_to_update[key] = sub_dict
        else:
            dict_to_update[key] = updates[key]
    return dict_to_update


class Model(object):
    """Base class for storage API models."""

    def __init__(self, **kwds):
        self.fields = list(kwds)
        for k, v in six.iteritems(kwds):
            setattr(self, k, v)

    def as_dict(self):
        d = {}
        for f in self.fields:
            v = getattr(self, f)
            if isinstance(v, Model):
                v = v.as_dict()
            elif isinstance(v, list) and v and isinstance(v[0], Model):
                v = [sub.as_dict() for sub in v]
            d[f] = v
        return d

    def __eq__(self, other):
        return self.as_dict() == other.as_dict()

    @classmethod
    def get_field_names(cls):
        fields = inspect.getargspec(cls.__init__)[0]
        return set(fields) - set(["self"])


class Connection(object):
    """Base class for alarm storage system connections."""

    # A dictionary representing the capabilities of this driver.
    CAPABILITIES = {
        'alarms': {'query': {'simple': False,
                             'complex': False},
                   'history': {'query': {'simple': False,
                                         'complex': False}}},
    }

    STORAGE_CAPABILITIES = {
        'storage': {'production_ready': False},
    }

    def __init__(self, conf, url):
        pass

    @staticmethod
    def upgrade():
        """Migrate the database to `version` or the most recent version."""

    @staticmethod
    def get_alarms(name=None, user=None, state=None, meter=None,
                   project=None, enabled=None, alarm_id=None,
                   alarm_type=None, severity=None, exclude=None):
        """Yields a lists of alarms that match filters.

        :param name: Optional name for alarm.
        :param user: Optional ID for user that owns the resource.
        :param state: Optional string for alarm state.
        :param meter: Optional string for alarms associated with meter.
        :param project: Optional ID for project that owns the resource.
        :param enabled: Optional boolean to list disable alarm.
        :param alarm_id: Optional alarm_id to return one alarm.
        :param alarm_type: Optional alarm type.
        :param severity: Optional alarm severity.
        :param exclude: Optional dict for inequality constraint.
        """
        raise aodh.NotImplementedError('Alarms not implemented')

    @staticmethod
    def create_alarm(alarm):
        """Create an alarm. Returns the alarm as created.

        :param alarm: The alarm to create.
        """
        raise aodh.NotImplementedError('Alarms not implemented')

    @staticmethod
    def update_alarm(alarm):
        """Update alarm."""
        raise aodh.NotImplementedError('Alarms not implemented')

    @staticmethod
    def delete_alarm(alarm_id):
        """Delete an alarm and its history data."""
        raise aodh.NotImplementedError('Alarms not implemented')

    @staticmethod
    def get_alarm_changes(alarm_id, on_behalf_of,
                          user=None, project=None, alarm_type=None,
                          severity=None, start_timestamp=None,
                          start_timestamp_op=None, end_timestamp=None,
                          end_timestamp_op=None):
        """Yields list of AlarmChanges describing alarm history

        Changes are always sorted in reverse order of occurrence, given
        the importance of currency.

        Segregation for non-administrative users is done on the basis
        of the on_behalf_of parameter. This allows such users to have
        visibility on both the changes initiated by themselves directly
        (generally creation, rule changes, or deletion) and also on those
        changes initiated on their behalf by the alarming service (state
        transitions after alarm thresholds are crossed).

        :param alarm_id: ID of alarm to return changes for
        :param on_behalf_of: ID of tenant to scope changes query (None for
                             administrative user, indicating all projects)
        :param user: Optional ID of user to return changes for
        :param project: Optional ID of project to return changes for
        :param alarm_type: Optional change type
        :param severity: Optional change severity
        :param start_timestamp: Optional modified timestamp start range
        :param start_timestamp_op: Optional timestamp start range operation
        :param end_timestamp: Optional modified timestamp end range
        :param end_timestamp_op: Optional timestamp end range operation
        """
        raise aodh.NotImplementedError('Alarm history not implemented')

    @staticmethod
    def record_alarm_change(alarm_change):
        """Record alarm change event."""
        raise aodh.NotImplementedError('Alarm history not implemented')

    @staticmethod
    def clear():
        """Clear database."""

    @staticmethod
    def query_alarms(filter_expr=None, orderby=None, limit=None):
        """Return an iterable of model.Alarm objects.

        :param filter_expr: Filter expression for query.
        :param orderby: List of field name and direction pairs for order by.
        :param limit: Maximum number of results to return.
        """

        raise aodh.NotImplementedError('Complex query for alarms '
                                       'is not implemented.')

    @staticmethod
    def query_alarm_history(filter_expr=None, orderby=None, limit=None):
        """Return an iterable of model.AlarmChange objects.

        :param filter_expr: Filter expression for query.
        :param orderby: List of field name and direction pairs for order by.
        :param limit: Maximum number of results to return.
        """

        raise aodh.NotImplementedError('Complex query for alarms '
                                       'history is not implemented.')

    @classmethod
    def get_capabilities(cls):
        """Return an dictionary with the capabilities of each driver."""
        return cls.CAPABILITIES

    @classmethod
    def get_storage_capabilities(cls):
        """Return a dictionary representing the performance capabilities.

        This is needed to evaluate the performance of each driver.
        """
        return cls.STORAGE_CAPABILITIES

    @staticmethod
    def clear_expired_alarm_history_data(alarm_history_ttl):
        """Clear expired alarm history data from the backend storage system.

        Clearing occurs according to the time-to-live.

        :param alarm_history_ttl: Number of seconds to keep alarm history
                                  records for.
        """
        raise aodh.NotImplementedError('Clearing alarm history '
                                       'not implemented')
