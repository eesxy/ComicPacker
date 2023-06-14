# Comic2Epub

多功能漫画epub打包器，包含分卷、过滤、裁边、去重等多种实用功能

## Dependency

需要`python>=3.7`，以及`numpy`,  `jinja2`, `imagededup`, `natsort`库

```bash
pip install numpy jinja2 imagededup natsort
```

## 基本用法

首先将漫画文件按照下述方式组织：

```
source_path
├───comic1
│   │   cover.jpg
│   ├───chapter1
│   │       image1.jpg
│   │       image2.jpg
│   │       ...
│   ├───chapter2
│   │       image1.jpg
│   │       image2.jpg
│   │       ...
│   └───...
├───comic2
│   └───...
└───...
```

1. 每部漫画组织为一个文件夹，包含各章节文件夹和一个封面图(可选)，封面图名称必须为`cover`

2. 每个章节文件夹包含该章节的所有图片，图片仅支持JPEG和PNG格式，其余格式的文件将被忽略
3. 所有漫画文件夹放在同一目录，修改配置文件中的`source_path`指向该目录

然后按需要修改配置文件`settings.toml`，各配置项的功能详见注释

最后转到项目目录，执行

```bash
python main.py
```

等待打包完成即可

## 功能介绍

### 目录和元数据

打包时会自动生成目录并添加元数据，用户可以指定漫画标题和各章节标题(必须)，以及作者、分类、简介等(可选)

用户需要以指定的方式组织这些信息，支持以下三种方式：

- `general`: 漫画文件夹的名称即为漫画标题，章节文件夹的名称即为章节标题，每个章节内的图片文件名按文件浏览器名称升序排序(即页面顺序与文件浏览器中一致)，不添加其他元数据
- `tachiyomi`: 与`general`类似，只是在各个漫画文件夹中包含一个Tachiyomi形式的`.json`格式元数据文件，通过该文件指定漫画标题、作者、分类和简介，文件内容形式见[Tachiyomi文档](https://tachiyomi.org/help/guides/local-manga/#editing-local-manga-details)
- `bcdown`: 专门适配[bcdown](https://github.com/lihe07/bilibili_comics_downloader)，用户无需手动指定任何信息
- `dmzjbackup`: 专门适配作者的另一个项目[Dmzj_backup](https://github.com/eesxy/Dmzj_backup)，用户无需手动指定任何信息

兼容大部分下载器的文件组织方式，包括作者的另一个项目[Dmzj_backup](https://github.com/eesxy/Dmzj_backup)~~(打个广告)~~

### 分卷

默认整部漫画打包为一个epub文件，也可以拆分为多个epub文件，支持以下两种拆分方式：

- 按固定章节数拆分，例如每10话生成一个epub文件

- 手动指定分卷方式，用户需要编写一个`.toml`文件，内容形如

  ```toml
  [comic_0]
  title = "example"
  breakpoints = ["第14话", "第29话"]
  
  [comic_1]
  ...
  ```

  其中`title`为待拆分的漫画标题，`breakpoints`为各分卷第一章节的标题(第一分卷可以省略)

### 过滤

按规则过滤漫画和章节，支持的规则如下：

- 过滤章节数过少的漫画，如新连载、一话短篇、客座连载等
- 过滤每章页数过少的漫画，如推特短漫等
- 过滤页数过多的章节，如单行本、画集等附加章节

### 裁边

裁剪图片的白边

~~(众所周知，叔叔家的芳文系四格白边大到能停航母，而且右下角会有水印，一般阅读器无法直接裁边，于是有了这个功能)~~

用户可以指定白边阈值，例如[0, 140]，灰度值在此闭区间内的视为有效内容，裁边模块会自动找到一个包含全部有效内容的最小矩形

### 去重

去除重复的页面，通常是重复的尾页，如汉化组信息、版权页等，对每话页数较少但含有尾页的漫画很有用

此功能基于[imagededup](https://github.com/idealo/imagededup)的图像hash方法

> **注意**：此项目不会完全去掉这些版权页，只是将这些页面移至最后并存放在单独的`copyright`章节；如果用户需要分发由此项目打包的epub文件，请确保这种处理方式符合版权方要求
>
> 此外，个人用户通过修改本项目源代码可以实现完全去除这些页面，并发布完全去除这些页面的分支；这一做法并不违反MIT许可，但作者希望您尽可能保留汉化组信息或版权页

### 降采样

对于尺寸过大的图片，降采样到适配指定的屏幕大小，可以有效减小文件大小

此功能原本是为分辨率有限的墨水屏设备设计的，但作者在墨水屏设备上实测发现，降采样后的图像的文字部分有时会比原图模糊，作者推测这可能是由于墨水屏上图像降采样算法与一般设备不同(尤其是16位灰阶下)，但不排除打包器本身有bug的可能，请谨慎启用此功能

## 设置

设置项详见配置文件`settings.toml`

### 多配置文件

有时需要对不同的图源使用不同的配置，可以创建新的配置文件，例如`mysettings.toml`，然后在运行时指定配置文件

```bash
python main.py -c mysettings.toml
```

## Acknowledgement

epub打包部分代码来自[comicepub](https://github.com/moeoverflow/comicepub)，特此致谢，已添加许可证

> 打包代码相比原仓库有以下修改：
>
> 1. 增加目录
> 2. 增加description元数据，不再指定author, publisher等元数据的默认值
> 3. 图片目录由单层改为章节-页面两层，便于解包后取得原目录结构
> 4. 默认语言由ja改为zh-CN

## TODO

后续可能会加一个按文件大小自动分卷的功能，因为部分阅读器只支持最大2GB的epub文件，这种情况下手动分卷比较繁琐，自动分卷容易拆分出太多分卷

## Licence

MIT
