function changeAddType()
{
    var obj = document.getElementById("addtype");
    var type = obj.options[obj.selectedIndex].value;
    var singleObj = document.getElementById("singleStudent");
    var batchObj = document.getElementById("batchStudent");
    // 如果选择了批量增加
    if (type == "batch")
    {
        // 隐藏单个增加的选项
        singleObj.style.visibility = "hidden";
        singleObj.style.position = "absolute";
        document.getElementById("student_id").removeAttribute("required");
        // 把批量增加的选项变为可见
        batchObj.style.visibility = "visible";
        batchObj.style.position = "relative";
        document.getElementById("student_file").setAttribute("required",true);
    }
    else
    {
        // 隐藏批量增加的选项
        batchObj.style.visibility = "hidden";
        batchObj.style.position = "absolute";
        document.getElementById("student_file").removeAttribute("required");
        // 把单个增加的选项变为可见
        singleObj.style.visibility = "visible";
        singleObj.style.position = "relative";
        document.getElementById("student_id").setAttribute("required", true);
    }
}

function changeDeleteType()
{
    var obj = document.getElementById("deletetype");
    var type = obj.options[obj.selectedIndex].value;
    var singleObj = document.getElementById("singleStudent");
    var batchObj = document.getElementById("batchStudent");
    // 如果选择了批量删除
    if (type == "batch")
    {
        // 隐藏单个删除的选项
        singleObj.style.visibility = "hidden";
        singleObj.style.position = "absolute";
        document.getElementById("student_id").removeAttribute("required");
        // 把批量删除的选项变为可见
        batchObj.style.visibility = "visible";
        batchObj.style.position = "relative";
        document.getElementById("student_file").setAttribute("required",true);
    }
    else
    {
        // 隐藏批量增加的选项
        batchObj.style.visibility = "hidden";
        batchObj.style.position = "absolute";
        document.getElementById("student_file").removeAttribute("required");
        // 把单个增加的选项变为可见
        singleObj.style.visibility = "visible";
        singleObj.style.position = "relative";
        document.getElementById("student_id").setAttribute("required", true);
    }
}

function changeAddPersonType()
{
    var obj = document.getElementById("addtype");
    var type = obj.options[obj.selectedIndex].value;
    var singlePersonIdObj = document.getElementById("singlePersonId");
    var singlePersonNameObj = document.getElementById("singlePersonName");
    var singlePersonEmailObj = document.getElementById("singlePersonEmail");
    var singlePersonPasswordObj = document.getElementById("singlePersonPassword");
    var batchPersonObj = document.getElementById("batchPerson");
    // 选择批量增加
    if (type == "batch")
    {
        // 隐藏单个增加的内容
        singlePersonIdObj.style.visibility = "hidden";
        singlePersonIdObj.style.position = "absolute";
        singlePersonNameObj.style.visibility = "hidden";
        singlePersonNameObj.style.position = "absolute";
        singlePersonEmailObj.style.visibility = "hidden";
        singlePersonEmailObj.style.position = "absolute";
        singlePersonPasswordObj.style.visibility = "hidden";
        singlePersonPasswordObj.style.position = "absolute";
        document.getElementById("id").removeAttribute("required");
        // 显示批量增加的内容
        batchPersonObj.style.visibility = "visible";
        batchPersonObj.style.position = "relative";
        document.getElementById("file").setAttribute("required", true);
    }
    else
    {
        // 隐藏批量增加的内容
        batchPersonObj.style.visibility = "hidden";
        batchPersonObj.style.position = "absolute";
        document.getElementById("file").removeAttribute("required");
        // 显示单个增加的内容
        singlePersonIdObj.style.visibility = "visible";
        singlePersonIdObj.style.position = "relative";
        singlePersonNameObj.style.visibility = "visible";
        singlePersonNameObj.style.position = "relative";
        singlePersonEmailObj.style.visibility = "visible";
        singlePersonEmailObj.style.position = "relative";
        singlePersonPasswordObj.style.visibility = "visible";
        singlePersonPasswordObj.style.position = "relative";
        document.getElementById("id").setAttribute("required", true);
    }
}

function changeDeletePersonType()
{
    var obj = document.getElementById("deletetype");
    var type = obj.options[obj.selectedIndex].value;
    var singlePersonObj = document.getElementById("singlePerson");
    var batchPersonObj = document.getElementById("batchPerson");
    // 批量删除
    if (type == "batch")
    {
        // 隐藏批量删除的内容
        singlePersonObj.style.visibility = "hidden";
        singlePersonObj.style.position = "absolute";
        document.getElementById("id").removeAttribute("required");
        // 显示批量删除的内容
        batchPersonObj.style.visibility = "visible";
        batchPersonObj.style.position = "relative";
        document.getElementById("file").setAttribute("required", true);
    }
    else
    {
        // 隐藏批量删除的内容
        batchPersonObj.style.visibility = "hidden";
        batchPersonObj.style.position = "absolute";
        document.getElementById("file").removeAttribute("required");
        // 显示批量删除的内容
        singlePersonObj.style.visibility = "visible";
        singlePersonObj.style.position = "relative";
        document.getElementById("id").setAttribute("required", true);
    }
}

// 判断输入页码是否符合范围
function validate_form(thisForm, pages)
{
    with(thisForm)
    {
        var re = /^[1-9]+[0-9]*$/;
        var p = page.value;
        // 检验输入页码是否是正整数
        if (!re.test(p))
        {
            alert("输入页码必须是正整数");
            return false;
        }
        // 检验输入页码是否在范围内
        if (p > pages || p < 1)
        {
            alert("输入页码范围必须是1~" + pages);
            return false;
        }
        return true;
    }
}

// 复选框的全选功能
function checkAll(obj)
{
    var checkList = document.getElementsByName("checkItem");
    for (var i = 0; i < checkList.length; i++)
        checkList[i].checked = obj.checked;
}

// 删除确认
function deleteConfirm(message)
{
    var checkList = document.getElementsByName("checkItem");
    // 查找是否有记录被选中
    var isChoose = false;
    for (var i = 0; i < checkList.length; i++)
        if (checkList[i].checked)
        {
            isChoose = true;
            break;
        }
    // 如果没有记录被选中，则不提交数据到后台
    if (!isChoose)
    {
        alert("请选择要删除的记录")
        return false;
    }
    // 确认是否要消除
    if (confirm(message))
        return true;
    return false;
}

// 根据屏幕高度设置div的最大高度
var height = $(window).height();
$(document).ready(function(){
    $("#divHeight").css("max-height", 0.65 * height + "px");
    $("#divHeight").css("overflow", "auto");
});