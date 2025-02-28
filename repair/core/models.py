from uuid import uuid4
from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser


class ServiceUser(AbstractUser):
    id = models.UUIDField(verbose_name="Идентификатор", default=uuid4, primary_key=True)
    is_serviceman = models.BooleanField(
        verbose_name="Ремонтник",
        default=False,
    )
    is_team_lead = models.BooleanField(
        verbose_name="Cтарший ремонтником",
        default=False,
    )

    def __str__(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username


class TokenData(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        verbose_name="Пользователь",
        on_delete=models.CASCADE,
        unique=True,
        related_name="token_data",
    )
    token = models.CharField(
        verbose_name="Токен",
        max_length=1500,
    )


class ServiceMan(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        verbose_name="Ремонтник",
        on_delete=models.CASCADE,
        unique=True,
        related_name="serviceman",
    )

    def __str__(self):
        return f"Ремонтник {self.user}"

    class Meta:
        verbose_name = "Ремонтник"
        verbose_name_plural = "Ремонтники"
        ordering = ["-id"]


class Order(models.Model):
    class GadgetType(models.TextChoices):
        TELEPHONE = ("TELEPHONE", "телефон")
        LAPTOP = ("LAPTOP", "ноутбук")
        TABLET = ("TABLET", "планшет")

    class RepairLvl(models.IntegerChoices):
        UNDEFINED = (0, "Неопределен")
        ONE = (1, "Внешний осмотр, диагностика")
        TWO = (2, "Ремонт с разбором телефона, замена не паяных деталей")
        THREE = (3, "Замена дисплея, тачскрина")
        FOUR = (4, "Электро-механический ремонт")

    class StatusEnum(models.TextChoices):
        CREATED = ("CREATED", "Заявка создана")
        GETTING_FROM_CLIENT = ("GETTING_FROM_CLIENT", "Получение техники от клиента")
        SENT_TO_REPAIR = ("SENT_TO_REPAIR", "Доставлен в службу ремонта")
        REPAIR_IN_PROCESS = ("REPAIR_IN_PROCESS", "Ремонт начат")
        REPAIR_DONE = ("REPAIR_DONE", "Ремонт закончен")
        SENDING_TO_CLIENT = ("SENDING_TO_CLIENT", "Доставка техники клиенту")
        CLOSED = ("CLOSED", "Заявка закрыта")

    serviceman = models.ForeignKey(
        ServiceMan,
        verbose_name="Ремонтник",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    id = models.UUIDField(verbose_name="Идентификатор заказа", primary_key=True)
    status = models.CharField(
        verbose_name="Статус заявки",
        max_length=48,
        choices=StatusEnum.choices,
        default=StatusEnum.CREATED,
    )
    category = models.CharField(
        "Техника",
        max_length=15,
        choices=GadgetType.choices,
    )
    serviceman_description = models.CharField(
        verbose_name="Комментарий ремонтника", max_length=1000, default="", blank=True
    )
    customer_description = models.CharField(
        verbose_name="Неисправность со слов клиента",
        max_length=1000,
        default="",
        blank=True,
    )
    deliveryman_description = models.CharField(
        verbose_name="Комментарий доставки", max_length=1000, default="", blank=True
    )
    created = models.DateTimeField(
        verbose_name="Дата и время создания заявки",
    )
    updated = models.DateTimeField(
        verbose_name="Дата и время редактирования заявки",
        auto_now=True,
        editable=False,
    )
    amount_due_by = models.FloatField(
        verbose_name="Сумма к оплате",
        default=0,
        null=True,
        blank=True,
    )
    payment_completed = models.BooleanField(
        verbose_name="Оплала произведена?",
        default=False,
    )

    model = models.CharField(
        verbose_name="Модель техники", max_length=1000, default="", blank=True
    )
    repair_lvl = models.IntegerField(
        verbose_name="Уровень ремонта",
        choices=RepairLvl.choices,
        default=0,
    )

    @staticmethod
    def get_for_user(user):
        valid_status = ["SENT_TO_REPAIR", "REPAIR_IN_PROCESS", "REPAIR_DONE"]
        if user.is_team_lead:
            queryset = Order.objects.all()
        else:
            queryset = Order.objects.filter(
                serviceman=user.serviceman, status__in=valid_status
            )

        return queryset

    def __str__(self):
        return f"Ремонт id={self.id}"

    class Meta:
        verbose_name = "Ремонт"
        verbose_name_plural = "Ремонты"
        ordering = ["-created"]


class Price(models.Model):
    category = models.CharField(
        verbose_name="Категория техники",
        max_length=48,
        choices=Order.GadgetType.choices,
        default="",
    )
    repair_lvl = models.IntegerField(
        verbose_name="Уровень ремонта",
        choices=Order.RepairLvl.choices,
        default=0,
    )
    price = models.FloatField(
        verbose_name="Стоимость ремонта",
        max_length=10,
        default=0,
    )

    def __str__(self):
        return f"Стоимость ремонта {self.repair_lvl} уровня для {self.category}"

    class Meta:
        verbose_name = "Стоимость ремонта"
        verbose_name_plural = "Стоимость ремонтов"
