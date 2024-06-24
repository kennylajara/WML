# import threading
# from typing import Type
#
#
# class Singleton(type):
#     """
#     A thread-safe implementation of Singleton.
#     """
#
#     _instances: dict[Type, object] = {}
#
#     def __call__(cls, *args, **kwargs):
#         """
#         Override the __call__ method to control the instantiation process.
#         Ensures only one instance of the class is created.
#         """
#         if cls not in cls._instances:
#             with cls._lock:
#                 if cls not in cls._instances:
#                     instance = super().__call__(*args, **kwargs)
#                     cls._instances[cls] = instance
#         return cls._instances[cls]
#
#     def __init__(cls, *args, **kwargs):
#         """
#         Initialize the Singleton class with a thread lock.
#         """
#         cls._lock = threading.Lock()
#         super().__init__(*args, **kwargs)
