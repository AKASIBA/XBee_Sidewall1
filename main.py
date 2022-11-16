# 巻上げ制御
import binascii
import xbee
import machine
import uio
import os
import time

ON = 5
OFF = 4
addr_coordinator = '\x00\x00\x00\x00\x00\x00\x00\x00'
xbee.atcmd('ID', 0x480)  # pan_id 480
xbee.atcmd('AV', 0x00)  # ADC_reference_1.25V
temp = machine.ADC('D1')
sl = str(binascii.hexlify(xbee.atcmd('SL')))[6:-1]
print(sl)
time.sleep(1)

drv = ["""&{'temp':'25','o_time':'07:00','c_time':'16:00','select':'21','wall':'21','everyday':'10',\
'remote':'10','button':'01'}""", """<body><h1><strong>くるファミ　AceDX</strong></h1><form name="Form" method="POST">\
<input name="cont_dev" value='""" + sl + """' hidden>""", """<p><input type="radio" id="select1" name="select" \
value='21' &> 手動<input type="radio" id="select2" name="select"  value='22' &> 自動</p>""",
       """<p><button class="button" name="button" value='02' type="submit" id="button"><strong>開</strong></button>""",
       """<button class="button" name="button" value='03' type="submit" id="button"><strong>閉</strong></button>\
 <button class="button" name="button" value='04' type="submit" id="button"><strong>停止</strong></button></p>""",
       """<input type="radio" name="wall" value="21" &>\
温度制御<input type="radio" name="wall" value="22" &> 時間制御</p>""",
       """<p>設定温度<input type="number" id="text" name="temp" value= $ min="0" max="35"> ℃</p>""", """<p>\
       <label>開く時刻  : <input type="time" id='time' name='o_time' value= $ required></p>\
<p><label>閉る時刻  : <input type="time" id='time' name='c_time' value= $ required></p>""",
       """<p><label>毎日同時刻に実行 :<input type="checkbox" name="everyday" id="text" value='11' &></label></p>""", """<p>\
       <label>リモート操作有効 :<input type="checkbox" name="remote" id="text" value='11' &></label></p>\
<p><button class="button" name="button" value='01' type="submit" id="button"><strong>実行</strong></button>""",
       """<button class="button" name="control" value='CANCEL' type="submit" id="button"><strong>戻る\
</strong></button></p></body></html>""", '?',
       """>if 'temp' in form:exe_dict['temp'] = '{:0>2}'.format(form.getvalue('temp'))@@""",
       """>if 'o_time' in form:exe_dict['o_time'] = '{:0>2}'.format(form.getvalue('o_time'))@@\
if 'c_time' in form:exe_dict['c_time'] = '{:0>2}'.format(form.getvalue('c_time'))@@""",
       """>exe_dict['select'] = '{:0>2}'.format(form.getvalue('select')) if form.getvalue('select') else '21'@@\
exe_dict['wall'] = '{:0>2}'.format(form.getvalue('wall')) if form.getvalue('wall') else '21'@@""",
       """>exe_dict['everyday'] = '{:0>2}'.format(form.getvalue('everyday'))if form.getvalue('everyday')else '10' @@""",
       """>exe_dict['remote'] = '{:0>2}'.format(form.getvalue('remote')) if form.getvalue('remote') else '10'@@""",
       """>if 'button' in form:exe_dict['button'] = '{:0>2}'.format(form.getvalue('button'))@@""", '@']


# drv.append("""<script>function sel1(ischecked){if(ischecked == true){document.getElementById("se1").disabled = false;\
# document.getElementById("se2").disabled = true;} else {document.getElementById("se1").disabled = \
# true;document.getElementById("se2").disabled = false; }}""")
# drv.append("""<script>function sel2(ischecked){if(ischecked == true){\
#            document.getElementById("se2").disabled = false;\
#            document.getElementById("se1").disabled = true;} else {""")
# drv.append("""<script>document.getElementById("se2").disabled = true;\
#            document.getElementById("se1").disabled = false;}}</script></body></html>""")


def xb_join():
    while True:
        status = xbee.atcmd('AI')  # network_join
        print('.', end='')
        if status == 0x00:
            # status = 0x01
            print('\nJoin!')
            break
        xbee.atcmd('CB', 0x01)  # commissioning_1
        time.sleep(2)


def pin_ini():
    xbee.atcmd('d2', OFF)
    xbee.atcmd('d3', OFF)
    xbee.atcmd('d6', OFF)


def packet_receive(com):
    packet = xbee.receive()
    if packet:
        payload = str(packet['payload'].decode('utf-8'))
    else:
        payload = com
    return payload


def send_driver():
    print('install_command')
    for i in drv:
        print(i)
        xbee.transmit(addr_coordinator, i)
        time.sleep_ms(100)
    print('send!')


def main():
    pin_ini()
    now_time = 0
    s_time = 0
    p_time = 0
    temp_c = ''
    o_time = ''
    c_time = ''
    select = ''
    wall = ''
    everyday = ''
    remote = ''
    button = ''
    d = True
    p = True
    t0 = 0
    s_w = 0
    mes_c = 'C0100001リモート　OFF'
    conf = ''
    c1 = True
    w_s = True
    time_w = 0
    k_time = 0
    try:
        f = uio.open('conf.txt', mode='r')
        conf = f.read()
        f.close()
    except OSError as e2:
        print('初期化ファイル読み込み失敗', e2)
    while True:
        t = time.ticks_ms()
        if t0 <= t or t0 - t >= 3000:  #
            t0 = t + 1000
            if now_time >= 86400:
                now_time = 0
                p_time = 0
            now_time = now_time + 1
            s_w = 0
            s_time = int(now_time / 60)
        temp_a = temp.read() * 0.030525 - 48.3
        command = packet_receive(conf)
        conf = ''
        if command:
            print(command)
            if command == 'sibainu':
                send_driver()
            elif command[0:2] == '99':
                now_time = int(command[-6:])
                s_time = int(now_time / 60)
                c1 = False
            else:
                try:
                    now_time = int(command[-6:])
                    s_time = int(now_time / 60)
                    temp_c = int(command[0:2])
                    o_time = int(command[2:4]) * 60 + int(command[5:7])
                    c_time = int(command[7:9]) * 60 + int(command[10:12])
                    select = command[12:14]
                    wall = command[14:16]
                    everyday = command[16:18]
                    remote = command[18:20]
                    button = command[20:22]
                    d = True
                    try:
                        os.remove('conf.txt')
                    except OSError as e4:
                        print('初期化ファイル消去失敗', e4)
                    f = uio.open('conf.txt', mode='w')
                    f.write(command)
                    f.close()
                    if c1:
                        try:
                            time.sleep(5)
                            xbee.transmit(addr_coordinator, 'S')
                            print('time calibration')
                        except OSError as e2:
                            print('時刻取得失敗', e2)
                except Exception as e3:
                    print('コマンド代入エラー', e3)
            if remote == '11':
                xbee.atcmd('d6', ON)
                mes_c = 'リモート　ON'
                if select == '21':
                    if button == '02':
                        xbee.atcmd('d3', OFF)
                        xbee.atcmd('d2', ON)
                        print('OPEN')
                    elif button == '03':
                        xbee.atcmd('d2', OFF)
                        xbee.atcmd('d3', ON)
                        print('CLOSE')
                    elif button == '04':
                        xbee.atcmd('d2', OFF)
                        xbee.atcmd('d3', OFF)
                        print('OFF')
                elif select == '22':
                    if wall == '21':
                        mes_c = "C0100001巻上温度:" + str(temp_c) + '℃'

                    if wall == '22' and (d or everyday == '11'):
                        mes_c = "C0100001巻上時間:" + '(' + command[2:7] + '-' + command[7:12] + ')'

            else:
                xbee.atcmd('d6', OFF)
                mes_c = 'C0100001リモート　OFF'
        if p_time <= now_time:
            p_time = now_time + 30
            if remote == '11' and select == '22':  # 自動
                if wall == '21':  # 温度
                    if temp_c <= temp_a and k_time <= s_time:
                        xbee.atcmd('d3', OFF)
                        xbee.atcmd('d2', ON)
                        print('o_open')
                        if w_s:
                            time_w = now_time + 5
                            w_s = False
                        if time_w <= now_time:
                            xbee.atcmd('d2', OFF)
                            w_s = True
                            k_time = s_time + 5
                    elif temp_c >= temp_a + 5 and k_time <= s_time:  # ヒステリシス　5
                        xbee.atcmd('d2', OFF)
                        xbee.atcmd('d3', ON)
                        print('o_close')
                        if w_s:
                            time_w = now_time + 5
                            w_s = False
                        if time_w <= now_time:
                            xbee.atcmd('d3', OFF)
                            w_s = True
                            k_time = s_time + 5
                elif wall == '22' and (d or everyday == '11'):  # 時間
                    if o_time <= s_time <= c_time:
                        xbee.atcmd('d3', OFF)
                        xbee.atcmd('d2', ON)
                        if p:
                            print('t_open')
                            p = False
                    elif s_time >= c_time:
                        xbee.atcmd('d2', OFF)
                        xbee.atcmd('d3', ON)
                        print('t_close')
                        p = True
                        if everyday == '11':
                            d = True

                        else:
                            d = False
                            mes_c = "C0100001リモート ON"
            mes_a = "{0:.1f}".format(temp_a) + '℃' + "\x00"
            mes_a = 'A01' + "{:05.1f}".format(temp_a) + '温度:' + mes_a
            print(s_time)
            print(mes_c)
            print(mes_a)
            print('o:', o_time, 'c:', c_time)  #
            try:
                xbee.transmit(addr_coordinator, mes_c)
                time.sleep(5)
                xbee.transmit(addr_coordinator, mes_a)
            except OSError as e5:
                print('メッセージ送信失敗', e5)
            if (s_time % 10) == 0:
                time.sleep(5)
                try:
                    xbee.transmit(addr_coordinator, 'S')
                    print('time calibration')
                except OSError as e2:
                    print('時刻取得失敗', e2)
        """       
            if now_time == 35340 and s_w == 0:
                s_w = 1
                try:
                    xbee.transmit(addr_coordinator, 'S')
                    print('time calibration')
                except OSError as e6:
                    print('時刻取得失敗', e6)
        """


try:
    main()
except Exception as e:
    print('other', e)
    time.sleep(10)
    machine.reset()
