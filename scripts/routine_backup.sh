log_file="/root/routine_backup.log"

# 备份到本地空间中
echo "[$(date +"%Y-%m-%d %H:%M:%S")] backup at /bpfs/v2_mnt/HCG/liweikang02/routine_backup/routine_backup.tar.gz" >> $log_file
bash /root/workdir/backup.sh /root/workdir /root/routine_backup.tar.gz >> $log_file;

# 备份到bpfs上
source ~/.bpfs_env
cp /root/routine_backup.tar.gz /bpfs/v2_mnt/HCG/liweikang02/routine_backup >> $log_file
echo "[$(date +"%Y-%m-%d %H:%M:%S")] backup succeed!" >> $log_file

# 清除物理空间
rm /root/routine_backup.tar.gz
echo "[$(date +"%Y-%m-%d %H:%M:%S")] clean physical place!" >> $log_file