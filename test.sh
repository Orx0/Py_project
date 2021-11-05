#!/bin/bash

banner()
{
  echo "+------------------------------------------+"
  printf "| %-46s | \n" "`date`"
  echo "|                                          |"
  printf "| %-40s | \n" "`cat /etc/redhat-release`"
  echo "+------------------------------------------+"
}
banner

echo ">请选择执行的功能<"

select()
{
    echo"1.服务器测试"
    echo"2.一键关闭selinux&firewall并同步时间"
    echo"3.单独进行硬盘测试（fio）"
}

#服务器测试
test()
{
    bash ./Config_inc.sh
}

#一键关闭
close()
{
    systemctl stop firewalld
    systemctl disable firewalld
    sed -i 's#SELINUX=enforcing#SELINUX=disabled#' /etc/sysconfig/selinux && echo 'selinux is disabled'
    ntpdate -u time.windows.com && hwclock -w && echo 'date is synchronized'
}

#硬盘测试
hardtest()
{
    bash ./hardtest.sh
}