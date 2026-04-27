from django.contrib import admin
from .models import Elderly, Doctor, Device, Alert, Order, Visit, HealthData


@admin.register(Elderly)
class ElderlyAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'gender', 'phone', 'health_status', 'risk_level', 'grid_area', 'created_at']
    list_filter = ['gender', 'health_status', 'risk_level', 'grid_area']
    search_fields = ['name', 'phone', 'address', 'id_card']
    list_per_page = 20
    ordering = ['-created_at']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'gender', 'birth_date', 'id_card', 'phone', 'address')
        }),
        ('联系信息', {
            'fields': ('emergency_contact', 'emergency_phone')
        }),
        ('健康信息', {
            'fields': ('health_status', 'risk_level', 'chronic_diseases', 'allergies', 'medications')
        }),
        ('其他信息', {
            'fields': ('device_id', 'grid_area', 'focus_tags')
        }),
    )


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'phone', 'specialization', 'status', 'rating', 'hospital', 'created_at']
    list_filter = ['status', 'specialization']
    search_fields = ['name', 'phone', 'hospital']
    list_per_page = 20
    ordering = ['-created_at']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'phone', 'specialization', 'hospital')
        }),
        ('状态信息', {
            'fields': ('status', 'rating')
        }),
    )


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'type', 'serial_number', 'elderly_id', 'status', 'battery_level', 'last_active']
    list_filter = ['type', 'status']
    search_fields = ['name', 'serial_number', 'location']
    list_per_page = 20
    ordering = ['-created_at']
    
    fieldsets = (
        ('设备信息', {
            'fields': ('name', 'type', 'serial_number')
        }),
        ('关联信息', {
            'fields': ('elderly_id', 'location')
        }),
        ('状态信息', {
            'fields': ('status', 'battery_level', 'last_active')
        }),
    )


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ['id', 'elderly_id', 'alert_type', 'alert_level', 'title', 'status', 'workflow_stage', 'created_at']
    list_filter = ['alert_type', 'alert_level', 'status', 'workflow_stage', 'ai_level']
    search_fields = ['title', 'content', 'location']
    list_per_page = 20
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('elderly_id', 'alert_type', 'alert_level', 'title', 'content', 'location')
        }),
        ('状态信息', {
            'fields': ('status', 'workflow_stage')
        }),
        ('处理信息', {
            'fields': ('rectify_measures', 'rectify_at', 'revisit_plan_at', 'revisit_result', 'revisit_at', 'closed_at')
        }),
        ('AI信息', {
            'fields': ('ai_level', 'ai_confidence', 'ai_reasons', 'ai_source')
        }),
        ('系统信息', {
            'fields': ('event_id', 'created_at', 'updated_at')
        }),
    )


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'elderly_id', 'order_type', 'urgency', 'title', 'status', 'assigned_to', 'created_at']
    list_filter = ['order_type', 'urgency', 'status']
    search_fields = ['title', 'description']
    list_per_page = 20
    ordering = ['-created_at']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('elderly_id', 'order_type', 'urgency', 'title', 'description')
        }),
        ('状态信息', {
            'fields': ('status', 'assigned_to')
        }),
    )


@admin.register(Visit)
class VisitAdmin(admin.ModelAdmin):
    list_display = ['id', 'elderly_id', 'doctor_id', 'visit_type', 'visit_date', 'status', 'created_at']
    list_filter = ['visit_type', 'status']
    search_fields = ['notes']
    list_per_page = 20
    ordering = ['-visit_date']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('elderly_id', 'doctor_id', 'visit_type', 'visit_date')
        }),
        ('状态信息', {
            'fields': ('status', 'notes')
        }),
    )


@admin.register(HealthData)
class HealthDataAdmin(admin.ModelAdmin):
    list_display = ['id', 'elderly_id', 'heart_rate', 'blood_pressure_high', 'blood_pressure_low', 'blood_oxygen', 'temperature', 'recorded_at']
    list_filter = ['recorded_at']
    search_fields = ['elderly_id']
    list_per_page = 20
    ordering = ['-recorded_at']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('elderly_id', 'recorded_at')
        }),
        ('健康指标', {
            'fields': ('heart_rate', 'blood_pressure_high', 'blood_pressure_low', 'blood_oxygen', 'temperature')
        }),
        ('系统信息', {
            'fields': ('created_at',)
        }),
    )


admin.site.site_header = "老年人监护系统管理后台"
admin.site.site_title = "老年人监护系统"
admin.site.index_title = "欢迎访问老年人监护系统管理后台"
