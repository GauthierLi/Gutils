#!/bin/bash
backup_dir="/root/workdir"
log_file="/root/routine_backup.log"
physical_save_place="/root/routine_backup.tar.gz"
bpfs_place="/path/to/bpfs"

# 备份到本地空间中
echo "[$(date +"%Y-%m-%d %H:%M:%S")] backup at $physical_save_place" >> $log_file
bash /root/workdir/backup.sh $backup_dir $physical_save_place >> $log_file;

# 备份到bpfs上
source ~/.bpfs_env
cp $physical_save_place $bpfs_place >> $log_file
echo "[$(date +"%Y-%m-%d %H:%M:%S")] backup succeed!" >> $log_file

# 清除物理空间
rm $physical_save_place
echo "[$(date +"%Y-%m-%d %H:%M:%S")] clean physical place!" >> $log_file
