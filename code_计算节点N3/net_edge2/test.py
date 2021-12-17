# from xmlrpc.server import SimpleXMLRPCServer
# def respon_string(str):
#     return "get string :%s"%str
#
# if __name__ == '__main__':
#     s = SimpleXMLRPCServer(('0.0.0.0', 8080))
#     s.register_function(respon_string,"get_string")
#     s.serve_forever()
#     print(1)


def producer(c):
    n = 0
    while n < 5:
        n += 1
        print('producer {}'.format(n))
        r = c.send(n)
        print('consumer return {}'.format(r))


def consumer():
    r = ''
    while True:
        n = yield r
        if not n:
            return
        print('consumer {} '.format(n))
        r = 'ok'


if __name__ == '__main__':
    c = consumer()
    next(c)  # 启动consumer
    producer(c)

