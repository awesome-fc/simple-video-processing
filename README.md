## 简介

假设您是对视频进行简单的处理， 架构方案图如下：

![image](main.png)

如上图所示， 用户上传格式为 .mov, .mp4, .flv 格式的视频到 OSS 指定前缀目录(该示例是 video/inputs/), OSS 触发器自动触发函数执行， 函数调用 FFmpeg 进行视频转码(在该示例中是将视频统一转为 640*480 的 mp4)， 并且将转码后的视频保存回 OSS 指定的输出目录(该示例是 video/outputs/)。

## 操作部署

[免费开通函数计算](https://statistics.functioncompute.com/?title=ServerlessVideo&theme=ServerlessVideo&author=rsong&src=article&url=http://fc.console.aliyun.com)，按量付费，函数计算有很大的免费额度。

[免费开通对象存储 OSS](oss.console.aliyun.com/)

#### 1. clone 该工程

```bash
git clone  https://github.com/awesome-fc/simple-video-processing.git
```

进入 `simple-video-processing` 目录

#### 2. 安装并且配置最新版本的 funcraft

[fun 安装手册](https://github.com/alibaba/funcraft/blob/master/docs/usage/installation-zh.md)

在使用前，我们需要先进行配置，通过键入 fun config，然后按照提示，依次配置 Account ID、Access Key Id、Secret Access Key、 Default Region Name 即可

#### 3. 执行部署命令

- 更新 template.yml 文件
    > - 全局将 logproject `log-simple-transcode` 修改成另外一个日志服务全局唯一的名字， 有两处需要修改

    > - 全局将 BucketName `fc-hz-demo` 修改成自己的bucket

- 执行 `fun deploy`

#### 4. 注意

函数计算的执行环境有时间长度限制，如果 10 分钟不能满足您的需求， 您可以选择：

- 对视频进行分片 -> 转码 -> 合成处理， 详情参考：[fc-fnf-video-processing](https://github.com/awesome-fc/fc-fnf-video-processing/tree/master/video-processing)

- 联系函数计算团队(钉钉群号: 11721331) 或者提工单，适当放宽执行时长限制