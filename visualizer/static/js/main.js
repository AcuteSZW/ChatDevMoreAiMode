// 添加一条消息到聊天界面
function append_message(role, text, avatarUrl) {
  // 创建消息容器和头像元素
  var message_container = $("<div></div>").addClass("message-container");
  var avatar_element = $("<span></span>").addClass("avatar");
  var role_element = $("<p></p>").addClass("role").text(role);

  // 如果提供了头像 URL，则设置背景图片；否则使用绿色背景
  if (avatarUrl) {
    avatar_element.css("background-image", `url(${avatarUrl})`);
  } else {
    avatar_element.css("background-color", "green");
  }

  // 将角色和头像元素添加到消息容器
  message_container.append(role_element);
  message_container.append(avatar_element);

  // 根据角色解析消息内容
  var parsedText = role === 'System' ? parseSystemMessage(text) : parseCodeBlocks(text, role);

  // 将解析后的消息内容添加到消息容器
  message_container.append(parsedText);

  // 创建“复制”按钮
  var copyButton = $("<button></button>")
    .addClass("copy-button")
    .text("Copy")
    .click(function () {
      // 调用 copyToClipboard 函数复制消息内容
      copyToClipboard(parsedText);
      copyButton.text("Copied"); // 按钮文字变为“Copied”
      setTimeout(function () {
        copyButton.text("Copy"); // 5 秒后恢复为“Copy”
      }, 5000);
    });

  // 将“复制”按钮添加到消息容器
  message_container.append(copyButton);

  // 将消息容器添加到聊天框
  $("#chat-box").append(message_container);
}

// 解析代码块消息
function parseCodeBlocks(text, role) {
  // 使用正则表达式分割文本为代码块和普通文本
  var parts = text.split(/(```[\s\S]*?```)/g);
  var parsedText = $("<div></div>").addClass("message-text");

  // 遍历分割后的部分
  parts.forEach(part => {
    // 如果是代码块且角色不是系统
    if (part.startsWith("```") && role != "System") {
      var trimmedBlock = part.trim();
      var language = trimmedBlock.match(/^```(\w+)/); // 提取代码语言
      if (language) {
        language = language[1];
        var codeContent = trimmedBlock.replace(/^```(\w+)/, '').replace(/```$/, ''); // 提取代码内容
        var codeBlockHTML = `
          <div class="code-block">
            <div class="code-block-header">${role} - ${language}</div>
            <pre class="language-${language} dark line-numbers" data-line><code>${hljs.highlightAuto(codeContent, [language]).value}</code></pre>
          </div>
        `;
        // 添加代码块 HTML 到消息内容
        parsedText.append(codeBlockHTML);
      }
    } else {
      // 对普通文本部分进行 Markdown 渲染
      parsedText.append(marked(_.escape(part), { breaks: true }));
    }
  });

  return parsedText;
}

// 从服务器获取新消息
function get_new_messages() {
  // 发送 GET 请求到 /get_messages 接口
  $.getJSON("/get_messages", function (data) {
    // 获取当前已显示的消息数量
    var lastDisplayedMessageIndex = $("#chat-box .message-container").length;

    // 遍历新消息并添加到聊天框
    for (var i = lastDisplayedMessageIndex; i < data.length; i++) {
      var role = data[i].role;
      var text = data[i].text;
      var avatarUrl = data[i].avatarUrl;

      // 调用 append_message 添加消息
      append_message(role, text, avatarUrl);
    }
  });
}

// 解析系统消息，支持折叠和展开功能
function parseSystemMessage(text) {
  var message = $("<div></div>").addClass("message-text").addClass("system-message");
  var firstLine = text.split('\n')[0]; // 提取第一行作为摘要
  var collapsed = true; // 初始状态为折叠

  // 创建摘要内容
  var messageContent = $("<div></div>").html(marked(firstLine, { breaks: true })).addClass("original-markdown");
  // 创建完整消息内容
  var originalMarkdown = $("<div></div>").html(marked(text, { breaks: true })).addClass("original-markdown");

  // 创建“展开/折叠”按钮
  var expandButton = $("<button></button>")
    .addClass("expand-button")
    .text("Expand")
    .click(function () {
      // 切换折叠和展开状态
      if (collapsed) {
        messageContent.hide();
        originalMarkdown.show();
        expandButton.text("Collapse");
      } else {
        messageContent.show();
        originalMarkdown.hide();
        expandButton.text("Expand");
      }
      collapsed = !collapsed;
    });

  // 将内容和按钮添加到消息容器
  message.append(messageContent);
  message.append(originalMarkdown);
  message.append(expandButton);

  // 默认隐藏完整消息内容
  originalMarkdown.hide();

  return message;
}

// 将指定元素的文本内容复制到剪贴板
function copyToClipboard(element) {
  // 创建一个临时的 <textarea> 元素
  var tempTextArea = document.createElement("textarea");
  tempTextArea.value = element.text(); // 设置要复制的文本
  document.body.appendChild(tempTextArea);

  // 选中并复制文本
  tempTextArea.select();
  document.execCommand("copy");

  // 移除临时元素
  document.body.removeChild(tempTextArea);
}

// 页面加载完成后执行初始化操作
$(document).ready(function () {
  // 获取初始消息
  get_new_messages();
  // 每隔 1 秒获取新消息，实现实时更新
  setInterval(function () {
    get_new_messages();
  }, 1000);
});


