from fabric.api import *
from fabric.contrib.files import *
import os
from copy import copy
import time

"""
    Call this with fab -c .fab TASK to pick up deploy variables
    Required variables in .fab file:
        mail_server = x
        mail_port = x
        mail_username = x
        mail_password = x
        mail_default_sender = x
        mailer_debug = x
        mail_default_to = x
        mail_default_list = x
        webpass = x
        secret_key = x
        data_root = x
        rsync_ssh_user = x
        rsync_remote_host = x
        rsync_remote_path = x
        rsync_to_path = x
        dev_catalog_root = x
        prod_catalog_root = x
        mongo_db = x
        admins = x,y,z
        user_db_file = x
"""

code_dir = "/home/glider/glider-dac"

def deploy_dap():
    crontab_file = "/home/glider/crontab.txt"
    with settings(sudo_user='glider'):
        stop_supervisord(conf="/home/glider/supervisord.conf")
        with cd(code_dir):
            sudo("git pull origin master")
            update_libs(virtual_env="gliderdac")
            update_full_sync()
            update_crontab(src_file="deploy/glider_crontab.txt", dst_file=crontab_file)
        start_supervisord(conf="/home/glider/supervisord.conf", virtual_env="gliderdac")

def deploy_ftp():
    with settings(sudo_user='glider'):
        stop_supervisord(conf="/home/glider/supervisord.conf")
        with cd(code_dir):
            sudo("git pull origin master")
            update_supervisord(src_file="deploy/supervisord.conf", dst_file="/home/glider/supervisord.conf", virtual_env="gliderdac")
            update_libs(virtual_env="gliderdac")
            start_supervisord(conf="/home/glider/supervisord.conf", virtual_env="gliderdac")
            start_supervisor_processes(conf="/home/glider/supervisord.conf", virtual_env="gliderdac")

    stop_supervisord(conf="/root/supervisord-perms-monitor.conf", virtual_env="root-monitor")
    update_supervisord(src_file="deploy/supervisord-perms-monitor.conf", dst_file="/root/supervisord-perms-monitor.conf", virtual_env="root-monitor")
    update_libs(virtual_env="root-monitor")
    start_supervisord(conf="/root/supervisord-perms-monitor.conf", virtual_env="root-monitor")
    start_supervisor_processes(conf="/root/supervisord-perms-monitor.conf", virtual_env="root-monitor")

    restart_nginx()

def deploy_supervisord_dap():
    with settings(sudo_user='glider'):
        stop_supervisord(conf="/home/glider/supervisord.conf")
        update_supervisord('deploy/dap.supervisord.conf', '/home/glider/supervisord.conf', 'gliderdac')
        start_supervisord(conf="/home/glider/supervisord.conf", virtual_env="gliderdac")

def update_full_sync():
    # @BUG: same as in update_supervisord, need to do to temp location
    upload_template("scripts/full_sync.j2", "/tmp/full_sync", context=copy(env), use_jinja=True, use_sudo=False, backup=False, mirror_local_mode=True)
    sudo("cp /tmp/full_sync /home/glider/full_sync")

def update_crontab(src_file, dst_file):
    # @BUG: same
    upload_template(src_file, "/tmp/glider-crontab.txt", context=copy(env), use_jinja=True, use_sudo=False, backup=False, mirror_local_mode=True)
    sudo("cp /tmp/glider-crontab.txt %s" % dst_file)
    sudo("crontab %s" % dst_file)

def update_supervisord(src_file, dst_file, virtual_env=None):
    """
    Run from within with settings block setting sudo_user
    """
    if virtual_env is not None:
        with prefix("workon %s" % virtual_env):
            sudo("pip install supervisor")
    else:
        sudo("pip install supervisor")

    # @BUG: Fabric won't let you specify temp_dir to the underlying put call here, so it doesn't have perms to copy it out of the default
    #       temp location which is ec2-user's home. see https://github.com/fabric/fabric/pull/932
    # this is a workaround
    upload_template(src_file, "/tmp/sd.conf", context=copy(env), use_jinja=True, use_sudo=False, backup=False, mirror_local_mode=True)
    sudo("cp /tmp/sd.conf %s" % dst_file)

def update_libs(virtual_env=None):
    """
    Run from within with settings block setting sudo_user
    """
    with cd(code_dir):
        with settings(warn_only=True):
            if virtual_env is not None:
                with prefix("workon %s" % virtual_env):
                    sudo("pip install -r requirements.txt")
            else:
                sudo("pip install -r requirements.txt")

def restart_nginx():
    sudo("/etc/init.d/nginx restart")

def stop_supervisord(conf, virtual_env=None):
    """
    Run from within settings block setting sudo_user
    """
    with cd(code_dir):
        with settings(warn_only=True):
            if virtual_env is not None:
                with prefix("workon %s" % virtual_env):
                    sudo("supervisorctl -c %s stop all" % conf)
            else:
                sudo("supervisorctl -c %s stop all" % conf)
            sudo("kill -QUIT $(ps aux | grep supervisord | grep %s | grep -v grep | awk '{print $2}')" % conf)

    #kill_pythons()

def kill_pythons():
    with settings(warn_only=True):
        sudo("kill -QUIT $(ps aux | grep python | grep -v supervisord | awk '{print $2}')")

def start_supervisord(conf, virtual_env=None):
    """
    Run from within with settings block setting sudo_user
    """
    with cd(code_dir):
        with settings(warn_only=True):
            if virtual_env is not None:
                with prefix("workon %s" % virtual_env):
                    sudo("supervisord -c %s" % conf)
            else:
                sudo("supervisord -c %s" % conf)

def start_supervisor_processes(conf, virtual_env=None):
    """
    Run from within with settings block setting sudo_user
    """
    with cd(code_dir):
        with settings(warn_only=True):
            if virtual_env is not None:
                with prefix("workon %s" % virtual_env):
                    sudo("supervisorctl -c %s start all" % conf)
            else:
                sudo("supervisorctl -c %s start all" % conf)

def create_index():
    MONGO_URI = env.get('mongo_db')
    url = urlparse.urlparse(MONGO_URI)
    MONGODB_DATABASE = url.path[1:]

    run('mongo "%s" --eval "db.deployments.ensureIndex({\'name\':1}, {unique:true})"' % MONGODB_DATABASE)

def full_sync():
    with settings(sudo_user='glider'):
        with prefix("workon gliderdac"):
            sudo("~/full_sync")

def services(command="restart"):
    sudo("service tomcat-erddap-private %s" % command)
    sudo("service tomcat-erddap-public %s" % command)
    sudo("service tomcat-thredds %s" % command)
