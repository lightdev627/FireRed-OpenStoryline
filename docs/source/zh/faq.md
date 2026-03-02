# 最常问的问题

## 环境相关的问题

<details>
<summary><strong>问题 1: Conda 激活环境时发现脚本执行被禁止</strong></summary>

- **参考链接**：[https://juejin.cn/post/7349212852644954139](https://juejin.cn/post/7349212852644954139)
- **解决方法**： 在 PowerShell 中输入以下命令后重试：
    ```powershell
    Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
    ```

</details>


<details>
<summary>
<strong>问题 2: Windows 安装 Conda 后，创建虚拟环境时报错</strong></summary>

- **原因**: 这是由于安装时没有将 conda 加入到环境变量导致的。
- **解决方法**: 需要从开始菜单打开 Anaconda Prompt / Miniconda Prompt / Miniforge Prompt，cd 到当前目录，再创建环境。 
</details>