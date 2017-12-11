from redis import StrictRedis


class RedisTool(object):
    def __init__(self):
        self.sr = StrictRedis(port=6379)

    def spop_value(self, key_name):
        return self.sr.spop(key_name)

    def sismember_value(self, key_name, value):
        return self.sr.sismember(key_name, value)

    def sadd_value(self, key_name, value):
        return self.sr.sadd(key_name, value)

    def smembers(self, key_name):
        return self.sr.smembers(key_name)

    def sadd_iterable(self, key_name, iterable_values):
        for value in iterable_values:
            self.sadd_value(key_name, value)
