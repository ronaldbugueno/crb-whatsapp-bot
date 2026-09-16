"""
Archivo requerido por Passenger (el sistema que usa cPanel para correr apps Python).
No necesitas tocarlo: solo expone la app de Flask (definida en server.py) con el
nombre "application", que es lo que Passenger busca por convención.
"""

from server import app as application
