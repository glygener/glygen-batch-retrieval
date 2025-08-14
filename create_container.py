import os,sys
import string
from optparse import OptionParser
import glob
import json
import subprocess

__version__="1.0"
__status__ = "Dev"



###############################
def main():


    config_obj = json.load(open("conf/config.json"))
    image_name = config_obj["image_name"]
    container_name = config_obj["container_name"]
    data_dir = config_obj["data_dir"]

 
    cmd_list = []
    #cmd_list.append("sudo systemctl stop docker-glygen-retriever.service" )
        
    cmd_list.append("docker build --network=host -t %s ." % (image_name))
    for c in [container_name]:
        cmd = "docker ps --all |grep %s" % (c)
        container_id = subprocess.getoutput(cmd).split(" ")[0].strip()
        if container_id.strip() != "":
            cmd_list.append("docker rm -f %s " % (container_id))

    cmd = "docker create --name %s " % (container_name)
    cmd += " -v /var/run/docker.sock:/var/run/docker.sock -v /usr/bin/docker:/usr/bin/docker"
    cmd += " -v %s:%s %s" % (data_dir, data_dir, image_name) 
    cmd_list.append(cmd)

    cmd = "docker rm -f %s " % (container_name)
    cmd_list.append(cmd)
    cmd = "docker run -itd -v %s:%s --name %s %s" % (data_dir, data_dir, container_name, image_name)
    cmd_list.append(cmd)



    for cmd in cmd_list:
        print (cmd)
        x = subprocess.getoutput(cmd)
        print (x)


    #remove dangling images
    cmd = "docker images -f dangling=true"
    line_list = subprocess.getoutput(cmd).split("\n")
    for line in line_list[1:]:
        image_id = line.split()[2]
        cmd = "docker image rm -f " + image_id
        x = subprocess.getoutput(cmd)

    return



if __name__ == '__main__':
    main()
