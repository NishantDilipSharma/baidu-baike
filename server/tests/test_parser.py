"""Unit tests for Baidu Baike HTML parser and normalization."""

import pytest
from baidu_baike_mcp.parser import parse_baike_page

MOCK_HTML_NORMAL = """
<!DOCTYPE html>
<html>
<head><title>全过程人民民主_百度百科</title></head>
<body>
  <h1>全过程人民民主</h1>
  <div class="J-summary">
    “全过程人民民主”是社会主义民主政治的本质属性。
    <div class="lemma-subscribe">订阅</div>
  </div>
  <div class="basicInfo_pcW4Q J-basic-info">
    <dl class="basicInfoBlock_B_97h">
      <div class="itemWrapper_S9fE2">
        <dt class="basicInfoItem_DNnSi itemName_eE3Qn">中文名</dt>
        <dd class="basicInfoItem_DNnSi itemValue_AZDkL">全过程人民民主</dd>
      </div>
      <div class="itemWrapper_S9fE2">
        <dt class="basicInfoItem_DNnSi itemName_eE3Qn">范畴领域</dt>
        <dd class="basicInfoItem_DNnSi itemValue_AZDkL">社会政治学</dd>
      </div>
    </dl>
  </div>
  <div class="catalogList">
    <a class="catalogText">发展历程</a>
    <a class="catalogText">政治内涵</a>
  </div>
  <div class="J-lemma-content">
    <h2>发展历程播报编辑</h2>
    <div class="para">党的二十大报告把发展全过程人民民主确定为中国式现代化本质要求的一项重要内容[1]。</div>
    <h2>政治内涵</h2>
    <div class="para">全过程人民民主是社会主义民主政治的本质属性，具有丰富的时代内涵。</div>
  </div>
</body>
</html>
"""

MOCK_HTML_WAF = """
<!DOCTYPE html>
<html><head><title>百度安全验证</title></head><body>WAF challenge</body></html>
"""


def test_parse_normal_page():
    url = "https://baike.baidu.com/item/全过程人民民主"
    md = parse_baike_page(MOCK_HTML_NORMAL, url=url, fallback_lemma="全过程人民民主")

    assert "# 百度百科: 全过程人民民主" in md
    assert url in md
    assert "## 概述 (Summary)" in md
    assert "“全过程人民民主”是社会主义民主政治的本质属性。" in md
    assert "## 基本信息 (Infobox)" in md
    assert "- **中文名**: 全过程人民民主" in md
    assert "- **范畴领域**: 社会政治学" in md
    assert "1. 发展历程" in md
    assert "2. 政治内涵" in md
    assert "## 发展历程" in md
    assert "## 政治内涵" in md
    assert "党的二十大报告把发展全过程人民民主确定为中国式现代化本质要求的一项重要内容。" in md
    assert "播报" not in md
    assert "编辑" not in md
    assert "订阅" not in md


def test_parse_waf_page():
    url = "https://baike.baidu.com/item/test"
    md = parse_baike_page(MOCK_HTML_WAF, url=url, fallback_lemma="test")
    assert "Error: Baidu security verification triggered" in md


def test_truncation():
    url = "https://baike.baidu.com/item/test"
    md = parse_baike_page(MOCK_HTML_NORMAL, url=url, fallback_lemma="test", max_sections=1)
    assert "当前已显示前 1 个主要章节" in md
    assert "## 发展历程" in md
    assert "## 政治内涵" not in md
