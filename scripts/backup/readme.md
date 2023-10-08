# 1.代码备份
paddle cloud 目前通过死循环最多保存60天，加上内存限制很容易导致容器崩溃，可以经常使用以下脚本控制备份，并且避开大文件打包代码。（如果直接对所有文件进行打包，可能会导致内存不够容器爆炸，如：checkpoint文件达到了600G，备份后文件加上原文件将超过1T内存限制。此方法适用于开发过程中随手备份，或每日备份使用，代码调试无误后还是尽快提交到 icode 为好。）

```bash
#!/bin/bash

# 目标路径
TARGET_DIR=$1
# 输出的tar文件名
OUTPUT_NAME=$2
# packignore文件位置
PACKIGNORE_FILE=".packignore"

shift 2
# 检查是否还有其他参数，如果有，将它们分配给EXTRA变量
if [ "$#" -gt 0 ]; then
    EXTRA="$@"
else
    EXTRA=""
fi

echo "cd "$TARGET_DIR""
cd "$TARGET_DIR"

# 如果不存在packignore文件，给出警告
if [[ ! -f "${PACKIGNORE_FILE}" ]]; then
    echo "No ${PACKIGNORE_FILE} found!"
    exit 1
fi

# 将.packignore的模式转换为适用于find的模式
exclude_items=()
while IFS= read -r line; do
    # 跳过空行和注释
    [[ -z "$line" || $line == \#* ]] && continue
    # 判断是排除目录还是文件
    if [[ $line == *"/" ]]; then  # 排除目录
        while IFS= read -r -d $'\0' dir; do
            exclude_items+=("--exclude=$TARGET_DIR/${dir#${TARGET_DIR}/}")
        done < <(find "${TARGET_DIR}" -type d -name "${line%?}" -prune -print0)
    else  # 排除文件
        while IFS= read -r -d $'\0' file; do
            exclude_items+=("--exclude=$TARGET_DIR/${file#${TARGET_DIR}/}")
        done < <(find "${TARGET_DIR}" -type f -name "${line}" -print0)
    fi
done < "${PACKIGNORE_FILE}"

# 使用tar命令进行打包，同时排除指定的文件和文件夹
if [ "$EXTRA" == "" ]; then
    echo "tar czvf "${OUTPUT_NAME}" "${exclude_items[@]}" "${TARGET_DIR}""
    tar czvf "${OUTPUT_NAME}" "${exclude_items[@]}" "${TARGET_DIR}"
else
    echo "tar czvf "${OUTPUT_NAME}" "${exclude_items[@]}" "$EXTRA" "${TARGET_DIR}""
    tar czvf "${OUTPUT_NAME}" "${exclude_items[@]}" "$EXTRA" "${TARGET_DIR}"
fi

echo "Archive ${OUTPUT_NAME} created."
```

将.packignore文件放入需要备份的路径下。
```bash
*.egg-info/
log/
__pycache__/
*.pdparams
*.pth
*.zip
*.tar.gz
*.tar
```

运行如下命令即可备份(运行前记得给足权限)
```bash
chmod +x backup.sh
bash backup.sh /path/to/dir/need/backup /path/to/save/dir/name.tar.gz
```

**匹配规则：**
仅需更改.packignore内容，就可以通过脚本控制不需要备份的文件，目前支持：
1. 模糊匹配文件夹， 例子:  log*/ , __pycache__/
2. 模糊匹配文件,  例子:  *.log,  *remote*
3. 支持通过 --exclude = /path/to/file/or/dir 来排除文件或文件夹
匹配强制匹配所有目录以及子文件夹，不需要使用 **/log/的方式即可匹配多级目录；

## 1.2 自动备份
一个例子，配合上面的备份脚本，自动备份所有代码到 bpfs 中，并记录备份时间到 log_file 中. 修改好自己需要每日备份的路径，并给足权限
```bash
chmod +x routine_backup.sh
```

保存如下代码
```bash
#!/bin/bash
backup_dir="/want/to/backup/dir"
log_file="/root/routine_backup.log"
physical_save_place="/physical/place/for/routine_backup.tar.gz"
bpfs_place="/bpfs/dir/for/routine_backup"

# 备份到本地空间中
echo "[$(date +"%Y-%m-%d %H:%M:%S")] backup at $physical_save_place" >> $log_file
bash /path/to/backup.sh $backup_dir $physical_save_place >> $log_file;

# 备份到bpfs上
source ~/.bpfs_env
cp $physical_save_place $bpfs_place >> $log_file
echo "[$(date +"%Y-%m-%d %H:%M:%S")] backup succeed!" >> $log_file

# 清除物理空间
rm $physical_save_place
echo "[$(date +"%Y-%m-%d %H:%M:%S")] clean physical place!" >> $log_file
```

要定时运行 shell 文件，你可以使用 cron 服务。cron 允许用户在指定的时间和日期自动执行命令或脚本。
以下是如何使用 cron 来定时运行 shell 文件的步骤：
```bash
crontab -e
```

1. 这将打开一个编辑器，允许你编辑你的个人 crontab 文件。
2. 添加一个定时任务:
3. 在文件的末尾，添加一个新的行来指定何时运行你的脚本。cron 的格式是：

```bash
* * * * * /path/to/your/script.sh
```

4. 其中每个 * 分别代表：
    * 分钟 (0 - 59)
    * 小时 (0 - 23)
    * 月的第几天 (1 - 31)
    * 月份 (1 - 12)
    * 星期的第几天 (0 - 6)（0代表星期天）
5. 例如，如果你想要每天早上 6:30 运行你的脚本，你可以这样写：
```bash
30 6 * * * /path/to/your/script.sh
```

6. 保存并退出编辑器。
7. 这通常取决于你使用的编辑器。如果是 vi/vim，你可以按 Esc，然后输入 :wq 后按 Enter 来保存并退出。如果是 nano，你可以按 Ctrl + O 然后按 Enter 来保存，再按 Ctrl + X 退出。
8. 确保你的脚本是可执行的:
```bash
chmod +x /path/to/your/script.sh
```
9. 检查你的 crontab 设置:

```bash
crontab -l
```
10. 这将显示你的 `crontab` 文件的内容，确保你的定时任务已经添加。运行以下命令启动服务（每次修改crontab -e都重启一下服务，确保生效）。
```bash
service cron start
```

完成上述步骤后，cron 将会按照你设置的时间定时运行你的脚本。


**注意**: 

1.crontab 时间经常对不上，运行以下命令修改本地时间为上海时间。
```bash
cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime
service cron restart
```
2.对于一些系统，确保你的脚本在 shebang 行（例如 `#!/bin/bash`）开始，并确保所有需要的环境变量都被正确设置，因为 `cron` 不会加载完整的用户环境。

# 2. 环境备份

使用conda-pack备份环境
```bash
conda install conda-pack
```

打包方式三选一
```bash
# 把虚拟环境 my_env 打包为 my_env.tar.gz
conda pack -n my_env

# -o 参数指定打包路径和名称，把虚拟环境 my_env 打包为 out_name.tar.gz
conda pack -n my_env -o out_name.tar.gz

# 把某个特定路径的虚拟环境打包为 my_env.tar.gz
conda pack -p /explicit/path/to/my_env
```

备份后在conda环境中恢复
```bash
mkdir /path/for/anaconda3/envs && cd /path/for/anaconda3/envs
tar -zxvf /path/to/my/envs -C .
source ~/.bashrc
```
检查环境
```bash
conda info --env
conda activate my_env
conda list
```