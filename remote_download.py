import commands,os,sys
import pexpect
import time

#Run in CentOS
#put 'python /root/XKGLog/download_xkg_log.log &' to /etc/rc.d/rc.local for auto run.

g_version='1.0.0'
g_create_time='2015-04-20'

g_interval_time=3600*24*7          # 1 week download log files

g_server_addr='121.40.194.37'
g_server_user='root'
g_server_pwd='123QWEasd'

#g_server_logpath='/root/test'
g_server_logpath='/root/xkgsyslog/logs'
g_server_tarfilepath='/root/xkgsyslog/xkgsyslog.tar.gz'

g_local_logpath='/root/XKGLog'
g_local_logname='xkgsyslog.tar.gz'
g_true_local_logname=''   #Init here.

g_debug_switch=True
g_debug_log='/root/XKGLog/download_xkg_log.log'

g_execute_result_cmd='if [ x$? = x0 ];then echo "o""o""o""o""o";else echo "x""x""x""x""x";fi'

g_xkglog_lock='/var/lock/xkglog.lock'

def usage():
    print 'usage: python download_xkg_log.py'
    print '-h or --help for help'
    print '-q for quiet mode,don\'t write debug file to %s' % (g_debug_log) 
    print '-t show version'
    print 'Create by Freedom:huangzheng@sinosims.com\n'
    exit(0)

def show_version():
    print 'Version:%s' % (g_version)
    print "Create time:%s" % (g_create_time)
    print 'Create by Freedom:huangzheng@sinosims.com\n'
    exit(0)

def log_debug(context):
    if not g_debug_switch:
        return
    f = open(g_debug_log,'a')
    f.write(time.strftime("[%Y-%m-%d %H:%I:%S]:") + context)
    f.close()

def ssh_cmd(ip, user, passwd, cmd):
    ret = -1
    ssh = pexpect.spawn('ssh %s@%s "%s;%s"' % (user, ip, cmd, g_execute_result_cmd), timeout=100)
    try:
        i = ssh.expect(['password:', 'continue connecting (yes/no)?'], timeout=100)
        if i == 0:
            ssh.sendline(passwd)
        elif i == 1:
            ssh.sendline('yes\n')
            ssh.expect('password: ')
            ssh.sendline(passwd)
        i = ssh.expect(['ooooo','xxxxx',pexpect.TIMEOUT], timeout=3600*5)  #Maybe tar big file
        if i == 0:
            log_debug('Execute remote successful\n')
            ret = 0
        elif i == 1:
            log_debug('Execute remote failed\n')
            ret = -3
        elif i == 2:
            log_debug('Execute remote timeout\n')
            ret = -4
        else:
            log_debug('Execute remote unknow\n')
            ret = -5
        log_debug('read ssh_cmd result: [%s]\n' % ssh.before)
    except pexpect.EOF:
        log_debug("ssh EOF\n")
        ssh.close()
        ret = -1
    except pexpect.TIMEOUT:
        log_debug("ssh TIMEOUT\n")
        ssh.close()
        ret = -2
    return ret

def ssh_md5sum(ip, user, passwd, file):
    ret = ''
    ssh = pexpect.spawn('ssh %s@%s "md5sum %s"' % (user, ip, file), timeout=100)
    try:
        i = ssh.expect(['password:', 'continue connecting (yes/no)?'], timeout=100)
        if i == 0:
            ssh.sendline(passwd)
        elif i == 1:
            ssh.sendline('yes\n')
            ssh.expect('password: ')
            ssh.sendline(passwd)
        i = ssh.expect([file,pexpect.TIMEOUT], timeout=500)
        if i == 0:
            log_debug('get ssh_md5sum successful\n')
            ret = ssh.before.strip()
        elif i == 1:
            log_debug('get ssh_md5sum timeout\n')
        else:
            log_debug('get ssh_md5sum unknow\n')
    except pexpect.EOF:
        log_debug("ssh EOF\n")
        ssh.close()
    except pexpect.TIMEOUT:
        log_debug("ssh TIMEOUT\n")
        ssh.close()
    return ret

def get_valid_localname():
    localname = time.strftime("%Y-%m-%d.%H-%I-%S-")+g_local_logname
    while os.path.exists(g_local_logpath+'/'+localname):
        time.sleep(1)
        localname = time.strftime("%Y-%m-%d.%H-%I-%S-")+g_local_logname
    return localname

def scp_remote_logs(ip, user, passwd, remote_path, local_path):
    global g_true_local_logname
    ret = -1
    g_true_local_logname = get_valid_localname()
    ssh = pexpect.spawn('scp %s@%s:%s %s/%s' % (user, ip, remote_path, local_path, g_true_local_logname), timeout=3600)
    try:
        i = ssh.expect(['password:', 'continue connecting (yes/no)?'], timeout=3600)
        if i == 0:
            ssh.sendline(passwd)
        elif i == 1:
            ssh.sendline('yes\n')
            ssh.expect('password: ')
            ssh.sendline(passwd)
        r = ssh.read()
        log_debug('read scp result: [%s]\n' % r)
        ret = 0
    except pexpect.EOF:
        log_debug("scp EOF\n")
        ssh.close()
        ret = -1
    except pexpect.TIMEOUT:
        log_debug("scp TIMEOUT\n")
        ssh.close()
        ret = -2
    return ret

def safe_modify_dir():
    cmd = 'flock -x %s -c "mv %s %s.download;mkdir -p %s"' % (g_xkglog_lock, g_server_logpath, g_server_logpath, g_server_logpath)
    log_debug("use cmd:[%s] to safe modify dir\n" % (cmd))
    return ssh_cmd(g_server_addr, g_server_user, g_server_pwd, cmd)    

def tar_remote_logs():
    cmd = 'cd %s&&tar vfcz %s %s.download' % (g_server_logpath[0:g_server_logpath.rfind('/',)], g_server_tarfilepath, g_server_logpath[g_server_logpath.rfind('/',)+1:])
    log_debug("use cmd:[%s] to tar remote files\n" % (cmd))
    return ssh_cmd(g_server_addr, g_server_user, g_server_pwd, cmd)

def download_logs():
    return scp_remote_logs(g_server_addr, g_server_user, g_server_pwd, g_server_tarfilepath, g_local_logpath)

def del_remote_logs():
    cmd = '\\rm %s.download -rf;\\rm %s' % (g_server_logpath,g_server_tarfilepath) #This is dangerous commnds!!!
    ssh_cmd(g_server_addr, g_server_user, g_server_pwd, cmd)
    log_debug("use cmd:[%s]\n" % (cmd))
    log_debug('Delete remote files\n')

def already_today_download():
    rc, rs = commands.getstatusoutput('ls %s/%s*%s' % (g_local_logpath,time.strftime("%Y-%m-%d"),g_local_logname))
    if rc == 0:
        return True
    else:
        return False

def compare_files():
    remote_md5 = ssh_md5sum(g_server_addr, g_server_user, g_server_pwd, g_server_tarfilepath)

    localfile = '%s/%s' % (g_local_logpath, g_true_local_logname)
    rc, rs = commands.getstatusoutput('md5sum %s' % (localfile))
    if rc == 0:
        local_md5 = rs[0:rs.find(' ',)]
        return remote_md5 == local_md5
    else:
        log_debug('Get local md5 failed [%d],[%s]\n' % (rc,rs))

    return False
    

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == '-h' or sys.argv[1] == '--help':
            usage()
        elif sys.argv[1] == '-v':
            show_version()
        elif sys.argv[1] == '-q':
            g_debug_switch = False

    while True:
        log_debug('----------Start download logs----------\n')

        if not already_today_download():
            if safe_modify_dir() == 0:
                if tar_remote_logs() == 0 :
                    download_logs()
                    if compare_files() :
                        del_remote_logs()
                        log_debug('Save file:%s/%s\n' % (g_local_logpath, g_true_local_logname))
                        log_debug('----------download logs successful----------\n\n\n')
                    else:
                        log_debug('compare files failed\n')
                        log_debug('----------download logs failed----------\n\n\n')
                else:
                    log_debug('tar remote logs failed\n')
                    log_debug('----------download logs failed----------\n\n\n')
            else:
                    log_debug('Modify dir failed\n')
                    log_debug('----------download logs failed----------\n\n\n')
        else:
            log_debug('Already today download\n')
            log_debug('----------download logs failed----------\n\n\n')

        time.sleep(g_interval_time)
