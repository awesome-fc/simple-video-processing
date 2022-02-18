## 简介

本项目是[轻松构建基于 Serverless 架构的弹性高可用视频处理系统](https://yq.aliyun.com/articles/727684) 的示例工程。

假设您是对视频进行单纯的处理， 架构方案图如下：

![](https://img.alicdn.com/imgextra/i4/O1CN010YvKKD1E6MLoVE3Fd_!!6000000000302-2-tps-705-136.png)


当然您也可以给函数配置 OSS 触发器， 让 OSS 的事情自动触发:

![](https://img.alicdn.com/tfs/TB1sPfQzhD1gK0jSZFKXXcJrVXa-612-185.png)

如上图所示， 用户上传任意格式的视频到 OSS 指定前缀目录(该示例是 video/inputs/), OSS 触发器自动触发函数执行， 函数调用 FFmpeg 进行视频转码(在该示例中是将视频统一转为 640*480 的 mp4)， 并且将转码后的视频保存回 OSS 指定的输出目录(该示例是 video/outputs/)。

## 操作部署

[免费开通函数计算](https://statistics.functioncompute.com/?title=ServerlessVideo&theme=ServerlessVideo&author=rsong&src=article&url=http://fc.console.aliyun.com)，按量付费，函数计算有很大的免费额度。

[免费开通对象存储 OSS](oss.console.aliyun.com/)

#### 1. clone 该工程

```bash
$ git clone  https://github.com/awesome-fc/simple-video-processing.git
```

进入 `simple-video-processing` 目录

#### 2. 安装并且配置最新版本的 Serverless Devs

[Serverless Devs 安装手册](https://www.serverless-devs.com/docs/install)

#### 3. 应用部署

```bash
s deploy
```

> s deploy 过程中，自动帮您生成 SLS 日志仓库和 FC 所使用的 RAM role,  第一次部署的时候， S 工具使用的 accesss 请使用权限较大的 AK（能创建role 和 日志仓库） 

#### 4. 调用函数

1. 发起 5 次异步任务函数调用

```bash
$ s VideoTranscoder invoke -e '{"bucket":"my-bucket", "object":"480P.mp4", "output_dir":"a", "dst_format":"mov"}' --invocation-type async   --stateful-async-invocation-id my1-480P-mp4
VideoTranscoder/transcode async invoke success.
request id: bf7d7745-886b-42fc-af21-ba87d98e1b1c

$ s VideoTranscoder invoke -e '{"bucket":"my-bucket", "object":"480P.mp4", "output_dir":"a", "dst_format":"mov"}' --invocation-type async   --stateful-async-invocation-id my2-480P-mp4
VideoTranscoder/transcode async invoke success.
request id: edb06071-ca26-4580-b0af-3959344cf5c3

$ s VideoTranscoder invoke -e '{"bucket":"my-bucket", "object":"480P.mp4", "output_dir":"a", "dst_format":"flv"}' --invocation-type async   --stateful-async-invocation-id my3-480P-mp4
VideoTranscoder/transcode async invoke success.
request id: 41101e41-3c0a-497a-b63c-35d510aef6fb

$ s VideoTranscoder invoke -e '{"bucket":"my-bucket", "object":"480P.mp4", "output_dir":"a", "dst_format":"avi"}' --invocation-type async   --stateful-async-invocation-id my4-480P-mp4
VideoTranscoder/transcode async invoke success.
request id: ff48cc04-c61b-4cd3-ae1b-1aaaa1f6c2b2

$ s VideoTranscoder invoke -e '{"bucket":"my-bucket", "object":"480P.mp4", "output_dir":"a", "dst_format":"m3u8"}' --invocation-type async   --stateful-async-invocation-id my5-480P-mp4
VideoTranscoder/transcode async invoke success.
request id: d4b02745-420c-4c9e-bc05-75cbdd2d010f

```

2. 登录[FC 控制台](https://fcnext.console.aliyun.com/)

![](https://img.alicdn.com/imgextra/i4/O1CN01jN5xQl1oUvle8aXFq_!!6000000005229-2-tps-1795-871.png)

可以清晰看出每一次转码任务的执行情况:

- A 视频是什么时候开始转码的, 什么时候转码结束
- B 视频转码任务不太符合预期， 我中途可以点击停止调用
- 通过调用状态过滤和时间窗口过滤，我可以知道现在有多少个任务正在执行， 历史完成情况是怎么样的
- 可以追溯每次转码任务执行日志和触发payload
- 当您的转码函数有异常时候， 会触发 dest-fail 函数的执行，您在这个函数可以添加您自定义的逻辑， 比如报警
- ...

转码完毕后， 您也可以登录 OSS 控制台到指定的输出目录查看转码后的视频。


## 优势
基于函数计算构建 Serverless 音视频处理系统具有如下优势：

**1. 相比于通用的转码处理服务:**

- 超强自定义，对用户透明， 基于 FFmpeg 或者其他音视频处理工具命令快速开发相应的音视频处理逻辑
- 原有基于 FFmpeg 自建的音视频处理服务可以一键迁移
- 弹性更强， 可以保证有充足的计算资源为转码服务，比如每周五定期产生几百个 4G 以上的 1080P 大视频， 但是希望当天几个小时后全部处理完
- 各种格式的音频转换或者各种采样率自定义、音频降噪等功能， 比如专业音频处理工具 aacgain 和 mp3gain
- 可以和 serverless 工作流完成更加复杂、自定义的任务编排，比如视频转码完成后，记录转码详情到数据库，同时自动将热度很高的视频预热到 CDN 上， 从而缓解源站压力
- 更多的方式的事件驱动， 比如可以选择 OSS 自动触发(丰富的触发规则)， 也可以根据业务选择 MNS 消息(支持 tag 过滤)触发
- 在大部分场景下具有很强的成本竞争力
- 自定义视频处理流程中可能会有多种操作组合， 比如转码、加水印和生成视频首页 GIF。后续为视频处理系统增加新需求，比如调整转码参数，新功能发布上线对原来的视频转码任务无影响

**2. 相比于其他自建服务:**

- 毫秒级弹性伸缩，弹性能力超强，支持大规模资源调用，可弹性支持几万核.小时的计算力，比如 1 万节课半个小时完成转码
- 只需要专注业务逻辑代码即可，原生自带事件驱动模式，简化开发编程模型，同时可以达到消息(即音视频任务)处理的优先级，可大大提高开发运维效率
- 函数计算采用 3AZ 部署， 安全性高，计算资源也是多 AZ 获取， 能保证每个用户需要的算力峰值
- 开箱即用的监控系统， 如上面 gif 动图所示，可以多维度监控函数的执行情况，根据监控快速定位问题，同时给用户提供分析能力
- 在大部分场景下具有很强的成本竞争力， 因为在函数计算是真正的按量付费(计费粒度在百毫秒)， 可以理解为 CPU 的利用率为 100%

如果您关注成本比对分析， 可以关注 [轻松构建基于 Serverless 架构的弹性高可用视频处理系统](https://yq.aliyun.com/articles/727684) 中的 `更低的成本` 章节， 那边有完善的数据和分析。