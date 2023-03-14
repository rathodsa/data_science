"""
Class def
"""
from __future__ import print_function
import os
import time
import libvirt

from libs.ssh_defs import Setup_ssh
from libs.post_process import Test_class
from libs.kickstart import Kickstart_class
#from libs.push_lib import Push_image


#=============================================================================#
class Build_class(object):
    """a"""
    # pylint: disable=too-many-instance-attributes
    def __init__(self, cfg, img_node, copy_defs, logger, parent, lock_c, snap_c, no_shutdown):
        """Init"""
        # Passed in Variables
        self.cfg         = cfg
        self.img_node    = img_node
        self.logger      = logger
        self.copy_defs   = copy_defs
        self.parent      = parent
        self.lock_c      = lock_c
        self.snap_c      = snap_c
        self.no_shutdown = no_shutdown
        self.vm_data     = self.lock_c.vm_data
        self.hv_data     = self.lock_c.hv_data
        self.vm_name     = self.vm_data.hostname.split('.')[0]

        # Add keyfile here since its alot more code to do the dynamic var replace on database entries
        self.hv_data.keyfile = '%s/etc/id_rsa' % self.cfg.app_base_dir

        self.vm_path    = '%s/%s' % (self.hv_data.vm_base, self.vm_name)
        self.remotepath = str(self.vm_path)

        # Other variables
        self.error_occured = False
        self.domain_id     = None
        self.vm_online     = False
        self.location      = None
        self.cleanup_done  = False
        self.conn          = None
        self.cmd_output    = None

        # Other class calls
        self.ks_class   = Kickstart_class(parent=self, cfg=cfg, build_type=self.img_node.build_type, img_node=img_node,
                                          logger=logger, vm_data=self.vm_data)

        self.test_class = Test_class(parent=self, cfg=cfg, logger=logger, img_node=self.img_node, vm_data=self.vm_data)
        self.ssh        = Setup_ssh(parent=self, parms=self.hv_data, logger=self.logger)

        self._set_location()
        self._open_conn()
        # __init__

    #-------------------------------------------------------------------------#
    def _set_location(self):
        """Sets the location variable for virt-install"""
        vip_name = 'pd-yum-adc-01.us.oracle.com'
        os_major = int(self.img_node.os_major)
        os_minor = int(self.img_node.os_minor)
        os_arch  = self.img_node.os_arch

        if os_major == 8:
            self.location = 'http://%s/bootable/OracleLinux/OL%s/%s/baseos/base/%s' % (vip_name, os_major, os_minor, os_arch)
        elif os_major == 7 and os_minor == 4:
            self.location = 'http://%s/bootable/OracleLinux/OL%s/3/base/%s' % (vip_name, os_major, os_arch)
        else:
            self.location = 'http://%s/bootable/OracleLinux/OL%s/%s/base/%s' % (vip_name, os_major, os_minor, os_arch)
        # _set_location

    #-------------------------------------------------------------------------#
    def _open_conn(self):
        """opens the connection to the libvirt daemon on self.hv_data.hostname"""
        if self.img_node.build_type == 'qemu' or self.img_node.build_type == 'kvm':
            b_type = 'qemu'
        elif self.img_node.build_type == 'ovm' or self.img_node.build_type == 'xen':
            b_type = 'xen'
        else:
            self.logger.critical('Unknown build type %s, exiting' % self.img_node.build_type)

        b_type = 'qemu'

        url = '%s+ssh://root@%s/system' % (b_type, self.hv_data.hostname)
        self.logger.info('Attempting to connect to libvirt %s' % url)

        self.conn = libvirt.open(url)
        if self.conn is None:
            self.logger.critical('Failed to open connection to %s' % url)
        # _open_conn

    #-------------------------------------------------------------------------#
    def close_conn(self):
        """Closes self.conn if open"""
        if self.conn is not None:
            self.logger.debug('Closing libvirt connection to %s' % self.hv_data.hostname)
            self.conn.close()
        # close_conn

    #-------------------------------------------------------------------------#
    def _get_domid(self):
        """Sets the self.domain_id field"""
        self.domain_id = self.vm_name
#        max_wait = 600
#        counter  = 0
#        self.domain_id = None
#
#        if self.conn is None:
#            self._open_conn()
#
#        while counter < max_wait:
#            domains = self.conn.listAllDomains(0)
#
#            if len(domains) != 0:
#                for domain in domains:
#                    print('|%s|%s|%s' % (self.vm_name, domain.name(), domain.ID()))
#                    if domain.name() == self.vm_name:
#                        self.domain_id = domain.ID()
#                        self.logger.info('Domain id for %s is %s' % (self.vm_name, self.domain_id))
#                        break
#            if self.domain_id is not None:
#                self.logger.debug('Took %s seconds to get domain id' % counter)
#                counter = max_wait + 1
#            else:
#                self.logger.debug('No domain if found for %s.  Sleeping for 10 seconds' % self.vm_name)
#                counter += 10
#                time.sleep(10)
#
#        if self.domain_id is None:
#            self.logger.warn('No domain id found for %s' % self.vm_name)
#            self.call_error('No domain id found for %s' % self.vm_name)
        # _get_domid

    #-------------------------------------------------------------------------#
    def call_error(self, msg=None):
        """Proper close out def for failures"""
        if self.cleanup_done is False:
            self.logger.error('Kvm_class call_error triggered')
            self.cleanup_done = True
            if msg is not None:
                self.logger.error(msg=msg)
            self.close_conn()
            if self.no_shutdown is False:
                self.destroy()
#                self.remove()
            else:
                self.logger.warn('###############################################################################')
                self.logger.warn('# An error occured.  Leaving system up')
                self.logger.warn('# ssh to %s and do:' % self.vm_data.hypervisor)
                self.logger.warn('# virsh console %s' % self.vm_data.hostname)
                self.logger.warn('###############################################################################')

            self.ks_class.call_error()
            self.test_class.call_error()
            self.parent.call_error()
        # call_error

    #-------------------------------------------------------------------------#
    def initialize(self):
        """initialize variables that should not be done in __init__"""
        # Set the initial status
#        self._connect_ssh()
        self.check_status()
        # initialize

    #-------------------------------------------------------------------------#
#    def _connect_ssh(self):
#        """Initiates the ssh connection if not already done"""
#        if self.ssh.connected is False:
#            self.ssh.connect()
#        # _connect_ssh
#
#    #-------------------------------------------------------------------------#
#    def _close_ssh(self):
#        """Closes the ssh connection if not already done"""
#        if self.ssh.connected is True:
#            self.ssh.close()
#        # _close_ssh

    #-------------------------------------------------------------------------#
    def destroy(self):
        """Destroy the VM if running"""
        self.check_status()
        if self.vm_online is True:
            self.logger.warn('Destroying VM domain %s' % self.vm_name)
            self._bld_cmd(cmd='destroy %s' % self.vm_name)
            time.sleep(2)
            self.check_status()
        # destroy

    #-------------------------------------------------------------------------#
    def stop(self):
        """Stop the VM if running"""
        self.check_status()
        if self.vm_online is True:
            self.logger.info('Stoping VM domain %s' % self.vm_name)
            self._bld_cmd(cmd='shutdown %s' % self.vm_name)

            # loop for up to 5 minutes for VM to come down.  If not down, then destroy
            counter = 0

            while counter < 300:
                time.sleep(10)
                self.check_status()
                if self.vm_online is True:
                    counter += 10
                else:
                    counter = 301

            if self.vm_online is True:
                self.logger.warn('Could not shutdown, destroying VM %s' % self.vm_name)
                self.destroy()
        # stop

    #-------------------------------------------------------------------------#
    def bounce(self):
        """Restart the VM if it is online, start it if not"""
        self.logger.info('Bouncing VM %s' % self.vm_name)
        self.check_status()
        if self.vm_online is True:
            self.stop()
            # Wait for VM to come down
            self.logger.info('    Waiting for VM to shutdown')
            counter = 0
            while counter < 300:
                self.check_status()
                if self.vm_online is False:
                    counter = 301
                else:
                    time.sleep(5)
                counter += 5

        self.start()
        # bounce

    #-------------------------------------------------------------------------#
    def __wait_for_ssh__(self):
        """function"""
        loop_val = True
        max_wait = 600
        counter  = 0

        # Wait for ssh client to start now
        self.logger.info('    Waiting for ssh to start')
        while loop_val is True:
            cmd = '/usr/bin/nc -zv -w 2 %s 22' % self.vm_data.ip_addr
            ssh_running = os.system(cmd)
            if ssh_running == 0:
                self.logger.info("    System is up and ready for commands")
                loop_val = False
            else:
                self.logger.info('    Current wait time: %s seconds' % counter)
            if counter > max_wait:
                self.call_error('Max wait time %s exceeded, exiting!' % max_wait)

            time.sleep(10)
            counter += 10
        # __wait_for_ssh__

    #-------------------------------------------------------------------------#
    def handle_base_image(self):
        """Returns True if a base image build is required"""
        create_image = True
        tmp_path     = '%s/%s' % (self.hv_data.vm_base, self.img_node.img_template_name)

        # Kickstart always should build image
        if self.img_node.build_by == 'kickstart':
            create_image = True
            self.logger.info('Kickstarting image')
        elif os.path.exists(tmp_path):
            self.logger.info('%s exists, using that as template' % tmp_path)
            create_image = False

        return create_image
        # handle_base_image

    #-------------------------------------------------------------------------#
    def copy_base_image(self):
        """Copies the base image into the correct build location to build image"""
        src = '%s/templates/%s' % (self.hv_data.vm_base, self.img_node.img_template_name)
#        src = '%s/templates/ol%s-template-%s' % (self.hv_data.vm_base, self.img_node.os_major, self.img_node.build_type)
        dst = '%s/%s' % (self.hv_data.vm_base, self.vm_name)
        cmd = 'cp -a --sparse=always %s %s' % (src, dst)

        self.logger.info('Copying %s to %s on host %s' % (src, dst, self.hv_data.hostname))
        self.ssh.do_cmd(cmd=cmd, do_exit=True)
        # copy_base_image

    #-------------------------------------------------------------------------#
    def create_base_image(self):
        """Kickstarts the base image and moved it to the defined template directory"""
        # Make sure VM is down BEFORE kickstarting
        self.stop()

        # Kickstart VM
        self.create()

        # Make sure VM is down BEFORE doing move
        self.stop()

        # Move newly created VM to a template
        src = '%s/%s' % (self.hv_data.vm_base, self.vm_name)
        dst = '%s/templates/%s' % (self.hv_data.vm_base, self.img_node.img_template_name)
        cmd = 'mv -f %s %s' % (src, dst)

        self.logger.info('Moving %s to %s on host %s' % (src, dst, self.hv_data.hostname))
        self.ssh.do_cmd(cmd=cmd, do_exit=True)

        # Update md5sum in database
        self.lock_c.update_ks_md5sum(md5sum=self.ks_class.ks_file_md5sum)
        # create_base_image

    #-------------------------------------------------------------------------#
    def import_image(self):
        """Imports the template"""
        self.logger.info('Importing image %s' % self.vm_name)
        cmdl = ['/usr/bin/virt-install', '--import',
                '--name %s'  % self.vm_name,
                '--ram=%s'   % self.img_node.vm_ram,
                '--vcpus=%s' % self.img_node.vm_cpu,
                '--graphics none',
                '--mac=%s' % self.vm_data.hw_addr,
                '--noautoconsole',
                '--disk path=%s' % self.vm_path]
        cmd = " ".join(cmdl)
        self.ssh.do_cmd(cmd=cmd)
        # import_image

    #-------------------------------------------------------------------------#
    def build(self):
        """Builds the image VM and runs the test suite"""
        self.logger.info('CREATING Image BUILD for kvm')

#        if self.handle_base_image() is True:
#            self.create_base_image()

        self.stop()
        self.undefine()

        if self.img_node.build_by != 'kickstart':
            self.copy_base_image()
            self.import_image()
            self.__wait_for_ssh__()
            self.test_class.ts_preform_test()
            self.stop()
            self.undefine()
        # build

    #-------------------------------------------------------------------------#
    def _bld_cmd(self, cmd, do_exit=True):
        """Return stdout from passed cmd"""
        ncmd = '/usr/bin/virsh %s' % cmd
        ret  = self.ssh.do_cmd(cmd=ncmd, do_exit=do_exit)
        return ret
        # _bld_cmd

    #-------------------------------------------------------------------------#
    def start(self):
        """Ssh to the dom0 server and start the vm"""
        self.check_status()

        if self.vm_online is False:
            self.logger.info("Starting VM %s" % self.vm_name)
            cmd = 'start %s' % self.vm_name
            self._bld_cmd(cmd=cmd)
            time.sleep(2)
            self.check_status()
        else:
            self.logger.warn('VM %s is already running' % self.vm_name)
        # start

    #-------------------------------------------------------------------------#
    def list_defined_vms(self):
        """Returns a list of defined VMs"""
        ret = list()

        for line in self._bld_cmd(cmd='list --all'):
            words = line.split()
            if len(words) < 2:
                continue
            ret.append(words[1])
        return ret
        # list_defined_vms

    #-------------------------------------------------------------------------#
    def check_status(self):
        """
        Returns the status of the vm.
        Values:
            running - VM is currently running
            off     - VM is shutdown and is defined
            paused  - VM is in a paused state
            None    - VM is not defined
        """
        ret  = None
        self.logger.debug('Checking status of %s' % self.vm_name)
        data = self._bld_cmd(cmd='list --all')

        self.vm_online = False
#        self.domain_id = -1

        for line in data:
            words = line.split()
            if len(words) < 2:
                continue
            if words[1] == self.vm_name:
                ret = words[-1]
                if words[0].strip() != '-':
                    self.vm_online = True
#                    self.domain_id = int(words[0].strip())
                break
        return ret
        # check_status

    #-------------------------------------------------------------------------#
    def _extra_args_line(self):
        """Returns the proper extra-args line used by self.create"""
        args = list()
        args.append('ks=%s' % self.ks_class.ks_url)
        if self.img_node.build_type == 'kvm':
            args.append('console=tty0')
            args.append('console=ttyS0,115200')
        args.append('debug')
        args.append('serial')
        args.append('cmdline')
        args.append('ip=%s'      % self.vm_data.ip_addr)
        args.append('netmask=%s' % self.hv_data.netmask)
        args.append('gateway=%s' % self.hv_data.gateway)
        args.append('dns=%s'     % self.hv_data.dns)

        ret = '--extra-args="%s"' % " ".join(args)
        return ret
        # _extra_args_line

    #-------------------------------------------------------------------------#
    def console(self):
        """Display the console"""
        if self.domain_id is not None:
            cmd = '/usr/bin/virsh console %s' % self.domain_id
        else:
            self.logger.error('No domain id found, using host name instead')
            cmd = '/usr/bin/virsh console %s' % self.vm_name
        self.cmd_output = self.ssh.monitor_ssh_cmd(cmd=cmd, exit_on_error=False)
        # console

    #-------------------------------------------------------------------------#
    def undefine(self):
        """Undefines the VM from kvm server"""
        if self.vm_name in self.list_defined_vms():
            self._bld_cmd(cmd='undefine %s' % self.vm_name, do_exit=False)
        # undefine

    #-------------------------------------------------------------------------#
    def create(self):
        """
        Ssh to the dom0 server and create the vm.
        """
        self.logger.info('Kickstarting image for %s' % self.vm_name)
        cur_retry = 0
        lcmd      = list()
        lcmd.append('/usr/bin/virt-install')
        lcmd.append('--noautoconsole')
        lcmd.append('--arch=x86_64')
        lcmd.append('--virt-type %s'         % self.img_node.build_type)
        lcmd.append('--mac=%s'               % self.vm_data.hw_addr)
        lcmd.append('--name %s'              % self.vm_name)
        lcmd.append('--os-type=%s'           % self.img_node.os_type)
        lcmd.append('--ram=%s'               % self.img_node.vm_ram)
        lcmd.append('--vcpus=%s'             % self.img_node.vm_cpu)
        lcmd.append('--disk path=%s,size=%s' % (self.vm_path, self.img_node.vm_size))
        lcmd.append('--location %s'          % self.location)
        lcmd.append('--graphics none')
        lcmd.append(self._extra_args_line())
        cmd1 = " ".join(lcmd)

        # Setup the kickstart files
        self.ks_class.setup_kickstart()

        while cur_retry < self.cfg.max_rebuild_retries:
            self.destroy()
            self.undefine()

            self.logger.info('Creating VM %s' % self.vm_name)
            self.ssh.do_cmd(cmd=cmd1)
            self._get_domid()

            # Need to do this to get console to disconnect when powered down
            self.console()

            if self.ssh.exit_status != 0:
                found_retry = False
                for entry in self.cfg.retry_trigger_text:
                    if entry in self.cmd_output:
                        found_retry = True
                        break
                if found_retry is True:
                    self.logger.info('Retry string found in output, retrying build')
                    time.sleep(60)
                    cur_retry += 1
                else:
                    self.call_error('No retry entries found, failing job')
            else:
                self.logger.info('Creation succeeded')
                cur_retry = self.cfg.max_rebuild_retries
        # create

    #-------------------------------------------------------------------------#
    def rename(self):
        """Renames the remote image to the os version"""
        new_name = '%s/ol%su%s-%s' % (self.hv_data.vm_base, self.img_node.os_major, self.img_node.os_minor, os.getpid())
        self.logger.info('Renaming %s to %s' % (self.remotepath, new_name))
        self.ssh.do_cmd('mv %s %s' % (self.remotepath, new_name))
        self.remotepath = new_name
        # rename

    #-------------------------------------------------------------------------#
    def remove(self):
        """Completely removes the image from the remote system"""
        if self.ssh.connected is True:
            self.destroy()
            self.undefine()

            self.logger.info('Removing %s' % self.remotepath)
            self.ssh.do_cmd(cmd='rm -rf %s' % self.remotepath)
        else:
            self.logger.warn('Build_class.ssh is not connected.  Cannot remove remote image')
        # remove
    # Build_class
