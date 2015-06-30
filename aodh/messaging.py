# -*- coding: utf-8 -*-
# Copyright 2013 eNovance <licensing@enovance.com>
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

from oslo_config import cfg
from oslo_context import context
import oslo_messaging
from oslo_serialization import jsonutils

DEFAULT_URL = "__default__"
TRANSPORTS = {}


class RequestContextSerializer(oslo_messaging.Serializer):
    def __init__(self, base):
        self._base = base

    def serialize_entity(self, ctxt, entity):
        if not self._base:
            return entity
        return self._base.serialize_entity(ctxt, entity)

    def deserialize_entity(self, ctxt, entity):
        if not self._base:
            return entity
        return self._base.deserialize_entity(ctxt, entity)

    @staticmethod
    def serialize_context(ctxt):
        return ctxt.to_dict()

    @staticmethod
    def deserialize_context(ctxt):
        return context.RequestContext(ctxt)


class JsonPayloadSerializer(oslo_messaging.NoOpSerializer):
    @classmethod
    def serialize_entity(cls, context, entity):
        return jsonutils.to_primitive(entity, convert_instances=True)


def setup():
    oslo_messaging.set_transport_defaults('aodh')


def get_transport(url=None, optional=False, cache=True):
    """Initialise the oslo_messaging layer."""
    global TRANSPORTS, DEFAULT_URL
    cache_key = url or DEFAULT_URL
    transport = TRANSPORTS.get(cache_key)
    if not transport or not cache:
        try:
            transport = oslo_messaging.get_transport(cfg.CONF, url)
        except oslo_messaging.InvalidTransportURL as e:
            if not optional or e.url:
                # NOTE(sileht): oslo_messaging is configured but unloadable
                # so reraise the exception
                raise
            return None
        else:
            if cache:
                TRANSPORTS[cache_key] = transport
    return transport


def get_rpc_server(transport, topic, endpoint):
    """Return a configured oslo_messaging rpc server."""
    cfg.CONF.import_opt('host', 'aodh.service')
    target = oslo_messaging.Target(server=cfg.CONF.host, topic=topic)
    serializer = RequestContextSerializer(JsonPayloadSerializer())
    return oslo_messaging.get_rpc_server(transport, target,
                                         [endpoint], executor='eventlet',
                                         serializer=serializer)


def get_rpc_client(transport, retry=None, **kwargs):
    """Return a configured oslo_messaging RPCClient."""
    target = oslo_messaging.Target(**kwargs)
    serializer = RequestContextSerializer(JsonPayloadSerializer())
    return oslo_messaging.RPCClient(transport, target,
                                    serializer=serializer,
                                    retry=retry)


def get_notification_listener(transport, targets, endpoints,
                              allow_requeue=False):
    """Return a configured oslo_messaging notification listener."""
    return oslo_messaging.get_notification_listener(
        transport, targets, endpoints, executor='eventlet',
        allow_requeue=allow_requeue)


def get_notifier(transport, publisher_id):
    """Return a configured oslo_messaging notifier."""
    serializer = RequestContextSerializer(JsonPayloadSerializer())
    notifier = oslo_messaging.Notifier(transport, serializer=serializer)
    return notifier.prepare(publisher_id=publisher_id)
