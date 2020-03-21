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

在使用前，我们需要先进行配置，通过键入 fun config，然后按照提示，依次配置 Account ID、Access Key Id、Secret Access Key、 Default Region Name 即可:

![](https://img.alicdn.com/tfs/TB1qp7Oy7Y2gK0jSZFgXXc5OFXa-622-140.png)

#### 3. 部署

- 更新 template.yml 文件
    > - 全局将 logproject `log-simple-transcode` 修改成另外一个日志服务全局唯一的名字， 有两处需要修改

    > - 全局将 BucketName `fc-hz-demo` 修改成自己的bucket,  有三处需要修改

- 执行 `fun deploy `,  成功部署相应的函数和日志库

- 执行 `fun invoke simple-transcode-service/init-helper -e '{"project":"log-simple-transcode2"}'`, 自动创建 custom-dashboard
    > 其中这里的 -e 参数中的 project 修改成您的 yml 中日志 project

- 手动[配置日志大盘](https://help.aliyun.com/document_detail/92647.html)
    ![](https://img.alicdn.com/tfs/TB1RhQLy5_1gK0jSZFqXXcpaXXa-1510-848.png)

完成上面步骤以后， 您可以在相应的 logproject 看到如下两个 dashboard:

![](https://img.alicdn.com/tfs/TB1XYIOy7T2gK0jSZFkXXcIQFXa-1516-766.png)

后面您可以往您配置的 bucket video/inputs 目录上传视频， 然后会触发函数进行视频的自动转码， 之后， 您将会获得如下音视频监控效果图:

<img src="transcode-monitor.gif?raw=true">

当然您可以参考这个 sample 构造更适合自己场景的自定义 dashboard， 对于该示例， 只需要打印具有如下key的json字符串即可

```python
json_log={
    "request_id": context.request_id,
    "video_name": object_key,
    "video_format": extension[1:],
    "size": M_size,
    "start_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(start_time_stamp+8*3600)),
    "end_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(end_time_stamp+8*3600)),
    "elapsed_time": elapsed_time,
    "processed_video_location": OUTPUT_DST,
}
print(json.dumps(json_log))
```

#### 4. 注意

因为音视频处理是强 CPU 密集型计算，强烈建议直接函数内存设置为 3G(2vCPU)， 当函数计算的执行环境有时间长度限制，如果 10 分钟不能满足您的需求， 您可以选择:

- 对视频进行分片 -> 转码 -> 合成处理， 详情参考：[fc-fnf-video-processing](https://github.com/awesome-fc/fc-fnf-video-processing/tree/master/video-processing)

- 联系函数计算团队(钉钉群号: 11721331) 或者提工单
    - 适当放宽执行时长限制
    - 申请使用更高的函数内存 12G(8vCPU)

#### 5. 总结
基于函数计算构建 Serverless 音视频处理系统具有如下优势：

**1. 相比于通用的转码处理服务:**

- 超强自定义，对用户透明， 基于 FFmpeg 或者其他音视频处理工具命令快速开发相应的音视频处理逻辑
- 原有基于 FFmpeg 自建的音视频处理服务可以一键迁移
- 弹性更强， 可以保证有充足的计算资源为转码服务，比如每周五定期产生几百个 4G 以上的大视频， 但是希望当天几个小时后全部处理完
- 各种格式的音频转换或者各种采样率自定义、音频降噪等功能， 比如专业音频处理工具 aacgain 和 mp3gain
- 可以和 serverless 工作流完成更加复杂、自定义的任务编排，比如视频转码完成后，记录转码详情到数据库，同时自动将热度很高的视频预热到 CDN 上， 从而缓解源站压力
- 更多的方式的事件驱动， 比如可以选择 OSS 自动触发(丰富的触发规则)， 也可以根据业务选择 MNS 消息(支持 tag 过滤)触发
- 在大部分场景下具有很强的成本竞争力

**2. 相比于其他自建服务:**

- 毫秒级弹性伸缩，弹性能力超强，支持大规模资源调用，可弹性支持几万核.小时的计算力，比如 1 万节课半个小时完成转码
- 只需要专注业务逻辑代码即可，原生自带事件驱动模式，简化开发编程模型，同时可以达到消息(即音视频任务)处理的优先级，可大大提高开发运维效率
- 函数计算采用 3AZ 部署， 安全性高，计算资源也是多 AZ 获取， 能保证每个用户需要的算力峰值
- 开箱即用的监控系统， 如上面 gif 动图所示，可以多维度监控函数的执行情况，根据监控快速定位问题，同时给用户提供分析能力， 比如视频的格式分布， size 分布等
- 在大部分场景下具有很强的成本竞争力， 因为在函数计算是真正的按量付费(计费粒度在百毫秒)， 可以理解为 CPU 的利用率为 100%