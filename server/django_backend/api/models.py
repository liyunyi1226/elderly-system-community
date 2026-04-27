from django.db import models


class Elderly(models.Model):
    name = models.CharField(max_length=100, verbose_name="姓名")
    gender = models.CharField(max_length=10, verbose_name="性别")
    birth_date = models.DateField(null=True, blank=True, verbose_name="出生日期")
    id_card = models.CharField(max_length=18, null=True, blank=True, verbose_name="身份证号")
    phone = models.CharField(max_length=20, null=True, blank=True, verbose_name="联系电话")
    address = models.CharField(max_length=200, null=True, blank=True, verbose_name="家庭地址")
    emergency_contact = models.CharField(max_length=100, null=True, blank=True, verbose_name="紧急联系人")
    emergency_phone = models.CharField(max_length=20, null=True, blank=True, verbose_name="紧急联系电话")
    health_status = models.CharField(max_length=50, default="良好", verbose_name="健康状态")
    risk_level = models.CharField(max_length=20, default="低风险", verbose_name="风险等级")
    chronic_diseases = models.TextField(null=True, blank=True, verbose_name="慢性病史")
    allergies = models.TextField(null=True, blank=True, verbose_name="过敏史")
    medications = models.TextField(null=True, blank=True, verbose_name="用药情况")
    device_id = models.IntegerField(null=True, blank=True, verbose_name="设备ID")
    grid_area = models.CharField(max_length=100, null=True, blank=True, verbose_name="网格区域")
    focus_tags = models.CharField(max_length=200, null=True, blank=True, verbose_name="关注标签")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = "elderly"
        verbose_name = "老人管理"
        verbose_name_plural = "老人管理"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.id})"


class Doctor(models.Model):
    name = models.CharField(max_length=100, verbose_name="姓名")
    phone = models.CharField(max_length=20, null=True, blank=True, verbose_name="联系电话")
    specialization = models.CharField(max_length=100, null=True, blank=True, verbose_name="专业领域")
    status = models.CharField(max_length=20, default="离线", verbose_name="状态")
    rating = models.FloatField(default=5.0, verbose_name="评分")
    hospital = models.CharField(max_length=200, null=True, blank=True, verbose_name="所属医院")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = "doctors"
        verbose_name = "医生管理"
        verbose_name_plural = "医生管理"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.id})"


class Device(models.Model):
    name = models.CharField(max_length=100, verbose_name="设备名称")
    type = models.CharField(max_length=50, verbose_name="设备类型")
    serial_number = models.CharField(max_length=100, unique=True, verbose_name="序列号")
    elderly_id = models.IntegerField(null=True, blank=True, verbose_name="关联老人ID")
    status = models.CharField(max_length=20, default="在线", verbose_name="状态")
    battery_level = models.IntegerField(default=100, verbose_name="电量百分比")
    last_active = models.DateTimeField(null=True, blank=True, verbose_name="最后活跃时间")
    location = models.CharField(max_length=200, null=True, blank=True, verbose_name="位置")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = "devices"
        verbose_name = "设备管理"
        verbose_name_plural = "设备管理"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.serial_number})"


class Alert(models.Model):
    elderly_id = models.IntegerField(verbose_name="老人ID")
    alert_type = models.CharField(max_length=50, verbose_name="警报类型")
    alert_level = models.IntegerField(default=1, verbose_name="警报级别")
    title = models.CharField(max_length=200, verbose_name="警报标题")
    content = models.TextField(verbose_name="警报内容")
    location = models.CharField(max_length=200, null=True, blank=True, verbose_name="位置")
    status = models.CharField(max_length=20, default="待处理", verbose_name="状态")
    workflow_stage = models.CharField(max_length=50, null=True, blank=True, verbose_name="工作流阶段")
    rectify_measures = models.TextField(null=True, blank=True, verbose_name="整改措施")
    rectify_at = models.CharField(max_length=50, null=True, blank=True, verbose_name="整改时间")
    revisit_plan_at = models.CharField(max_length=50, null=True, blank=True, verbose_name="回访计划时间")
    revisit_result = models.TextField(null=True, blank=True, verbose_name="回访结果")
    revisit_at = models.CharField(max_length=50, null=True, blank=True, verbose_name="回访时间")
    closed_at = models.CharField(max_length=50, null=True, blank=True, verbose_name="关闭时间")
    ai_level = models.CharField(max_length=20, null=True, blank=True, verbose_name="AI分级")
    ai_confidence = models.IntegerField(null=True, blank=True, verbose_name="AI置信度")
    ai_reasons = models.TextField(null=True, blank=True, verbose_name="AI原因")
    ai_source = models.CharField(max_length=50, null=True, blank=True, verbose_name="AI来源")
    event_id = models.CharField(max_length=100, null=True, blank=True, verbose_name="事件ID")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = "alerts"
        verbose_name = "警报管理"
        verbose_name_plural = "警报管理"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.id})"


class Order(models.Model):
    elderly_id = models.IntegerField(verbose_name="老人ID")
    order_type = models.CharField(max_length=50, verbose_name="工单类型")
    urgency = models.CharField(max_length=20, default="一般", verbose_name="紧急程度")
    title = models.CharField(max_length=200, verbose_name="工单标题")
    description = models.TextField(verbose_name="工单描述")
    status = models.CharField(max_length=20, default="待接单", verbose_name="状态")
    assigned_to = models.IntegerField(null=True, blank=True, verbose_name="分配给")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = "orders"
        verbose_name = "工单管理"
        verbose_name_plural = "工单管理"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.id})"


class Visit(models.Model):
    elderly_id = models.IntegerField(verbose_name="老人ID")
    doctor_id = models.IntegerField(null=True, blank=True, verbose_name="医生ID")
    visit_type = models.CharField(max_length=50, verbose_name="巡访类型")
    visit_date = models.DateField(verbose_name="巡访日期")
    notes = models.TextField(null=True, blank=True, verbose_name="巡访记录")
    status = models.CharField(max_length=20, default="已完成", verbose_name="状态")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = "visits"
        verbose_name = "巡访管理"
        verbose_name_plural = "巡访管理"
        ordering = ["-visit_date"]

    def __str__(self):
        return f"{self.visit_type} - {self.visit_date} ({self.id})"


class HealthData(models.Model):
    elderly_id = models.IntegerField(verbose_name="老人ID")
    heart_rate = models.IntegerField(null=True, blank=True, verbose_name="心率")
    blood_pressure_high = models.IntegerField(null=True, blank=True, verbose_name="收缩压")
    blood_pressure_low = models.IntegerField(null=True, blank=True, verbose_name="舒张压")
    blood_oxygen = models.FloatField(null=True, blank=True, verbose_name="血氧饱和度")
    temperature = models.FloatField(null=True, blank=True, verbose_name="体温")
    recorded_at = models.DateTimeField(verbose_name="记录时间")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        db_table = "health_data"
        verbose_name = "健康数据"
        verbose_name_plural = "健康数据"
        ordering = ["-recorded_at"]

    def __str__(self):
        return f"健康数据 - 老人ID:{self.elderly_id} ({self.recorded_at})"
