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