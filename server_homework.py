"""
Серверное приложение для соединений
"""
import asyncio
from asyncio import transports


class ClientProtocol(asyncio.Protocol):
    login: str
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server
        self.login = None

    # Метод для отображения 10 последних сообщений при успешном подключении в чат
    def send_history(self):
        for message in self.server.messages_history:
            self.transport.write(message.encode())

    def data_received(self, data: bytes):
        decoded = data.decode()
        print(decoded)

        if self.login is None:
            # login:User
            if decoded.startswith("login:"):
                # Проверяем логин на существование
                login_temp = decoded.replace("login:", "").replace("\r\n", "")
                if login_temp in self.server.client_logins:
                    self.transport.write(f"Логин {login_temp} занят, попробуйте другой".encode())    # Сообщаем клиенту об ошибке
                    # Разрываем соединение
                    self.transport.close()
                else:          # Если раньше логина не существовало, принимаем его на вход
                    self.login = login_temp
                    self.transport.write(
                     f"Привет, {self.login}!".encode()
                    )
                    self.server.client_logins.append(self.login)        # добавляем логин в список активных на сервере
                    self.send_history()     #Отправляем историю
        else:
            self.send_message(decoded)

    def send_message(self, message):
        format_string = f"<{self.login}> {message}"
        # Добавляю сообщение в список последних 10 сообщений. Если список становится слишком длинным, лишние элементы удаляю
        self.server.messages_history.append(format_string+'\n')
        if len(self.server.messages_history) > 10:
            del self.server.messages_history[0]

        encoded = format_string.encode()

        for client in self.server.clients:
            if client.login != self.login:
                client.transport.write(encoded)

    def connection_made(self, transport: transports.Transport):
        self.transport = transport
        self.server.clients.append(self)
        print("Соединение установлено")

    def connection_lost(self, exception):
        self.server.clients.remove(self)
        print("Соединение разорвано")


class Server:
    clients: list

    def __init__(self):
        self.clients = []
        self.client_logins = []     #список логинов активных сессий
        self.messages_history = []           #список 10 последних сообщений

    def create_protocol(self):
        return ClientProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.create_protocol,
            "127.0.0.1",
            8888
        )

        print("Сервер запущен ...")

        await coroutine.serve_forever()


process = Server()
try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")
