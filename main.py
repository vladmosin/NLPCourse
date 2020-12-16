import telebot
import pyowm
from pyowm.utils import timestamps

bot = telebot.TeleBot('1444765218:AAE0ilY-PZV9aInYCCnfr3tgQaa1EWqiLKI')


class State:
    def __init__(self):
        self.cities = set()
        self.days = set()
        self.greeting = False
        self.useless_iters = 0

    def parse_text(self, text):
        changed = self.__parse_day(text) or self.__parse_city(text)
        if not changed:
            self.useless_iters += 1
        else:
            self.useless_iters = 0

    def __parse_city(self, text):
        changed = False
        lower_text = text.lower()
        if 'москв' in lower_text:
            self.cities.add('Москва')
            changed = True

        if ('спб' in lower_text) or ('питер' in lower_text) or ('санкт-петербург' in lower_text) or ('петербург' in lower_text):
            self.cities.add('Санкт-Петербург')
            changed = True

        return changed

    def __parse_day(self, text):
        lower_text = text.lower()
        changed = False

        if 'сегодня' in lower_text:
            self.days.add('сегодня')
            changed = True

        if 'завтра' in lower_text:
            self.days.add('завтра')
            changed = True

        return changed

    def is_state_full(self):
        return len(self.days) > 0 and len(self.cities) > 0

    def get_request(self):
        prefix = 'Сообщите, пожалуйста, '
        if len(self.days) == 0 and len(self.cities) == 0:
            return prefix + 'дату и город.'

        if len(self.days) == 0:
            return prefix + 'дату (сегодня или завтра).'

        if len(self.cities) == 0:
            return prefix + 'город (СПб или Москва).'

    def collect_answer(self):
        answer = []
        for day in self.days:
            for city in self.cities:
                answer.append(f'Город: {city}, время: {day}, погода: {get_weather(city, day)} Цельсия')

        return "\n".join(answer)

    def clear(self):
        self.days = set()
        self.cities = set()
        self.greeting = False
        self.useless_iters = 0

    def greet(self):
        self.greeting = True
        return 'Здравствуйте!'

    def goodbye(self):
        return 'Всего хорошего!'

    def should_argue(self):
        return self.useless_iters >= 2


KEY = 'fa282a8335eb36884fb6ee92525536cb'
forecaster = pyowm.OWM(KEY)

longitudes = {'Москва': 37.618423, 'Санкт-Петербург': 30.308611}
latitudes = {'Москва': 55.751244, 'Санкт-Петербург': 59.937500}


def get_weather(city, day):
    weather = forecaster.weather_manager().one_call(lat=latitudes[city], lon=longitudes[city]).forecast_daily

    if day == 'сегодня':
        weather = weather[0]
    else:
        weather = weather[1]

    return weather.temperature(unit='celsius')['day']


state = State()


@bot.message_handler(content_types=['text'])
def react(message):
    if not state.greeting:
        bot.send_message(message.from_user.id, state.greet())

    text = message.text
    state.parse_text(text)

    if state.should_argue():
        bot.send_message(message.from_user.id, "К сожалению, Вы не сообщили никакой информации, попробуйте ещё раз.")

    if state.is_state_full():
        bot.send_message(message.from_user.id, state.collect_answer())
        bot.send_message(message.from_user.id, state.goodbye())
        state.clear()
    else:
        bot.send_message(message.from_user.id, state.get_request())


if __name__ == '__main__':
    bot.polling(none_stop=True, interval=0)