from django.db import models
from phonenumber_field.modelfields import PhoneNumberField

class Products(models.Model):
    idproducts = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    description = models.CharField(max_length=200)

    class Meta:
        db_table = "Products"
        verbose_name = "Product"
        verbose_name_plural = "Products"

    def __str__(self):
        return self.name


class Sell(models.Model):
    idsell = models.AutoField(
        db_column="idSell", primary_key=True
    )  # Field name made lowercase.
    datesell = models.DateTimeField(
        db_column="dateSell", auto_now=True
    )  # Field name made lowercase.
    totalsell = models.IntegerField(
        db_column="totalSell", blank=True, null=True
    )  # Field name made lowercase.
    id_product = models.ForeignKey(Products, on_delete=models.CASCADE, db_column="id_product")

    class Meta:
        managed = True
        db_table = "Sell"

    def __str__(self):
        return self.id_product.name


class SellProducts(models.Model):
    idsell_product = models.AutoField(
        db_column="idSell_Product", primary_key=True
    )  # Field name made lowercase.
    idsell = models.ForeignKey(
        Sell, models.DO_NOTHING, db_column="idSell"
    )  # Field name made lowercase.
    idproduct = models.ForeignKey(
        Products, models.DO_NOTHING, db_column="idProduct"
    )  # Field name made lowercase.
    quantity = models.IntegerField(null=False, blank=False)
    priceunitaty = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        managed = True
        db_table = "Sell_Products"

    def __str__(self):
        return self.idproduct.name

class Stock(models.Model):
    idstock = models.AutoField(primary_key=True)
    quantitystock = models.IntegerField()
    id_products = models.ForeignKey(
        Products, on_delete=models.CASCADE, db_column="id_Products"
    )  # Field name made lowercase.

    class Meta:
        managed = True
        db_table = "Stock"

    def __str__(self):
        return self.id_products.name


class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150)

    class Meta:
        managed = False
        db_table = "auth_group"


class AuthGroupPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey("AuthPermission", models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = "auth_group_permissions"
        unique_together = (("group", "permission"),)


class AuthPermission(models.Model):
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey("DjangoContentType", models.DO_NOTHING)
    codename = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = "auth_permission"
        unique_together = (("content_type", "codename"),)


class AuthUser(models.Model):
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.IntegerField()
    username = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.CharField(max_length=254)
    is_staff = models.IntegerField()
    is_active = models.IntegerField()
    date_joined = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "auth_user"


class AuthUserGroups(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = "auth_user_groups"
        unique_together = (("user", "group"),)


class AuthUserUserPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = "auth_user_user_permissions"
        unique_together = (("user", "permission"),)


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.PositiveSmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey(
        "DjangoContentType", models.DO_NOTHING, blank=True, null=True
    )
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = "django_admin_log"


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = "django_content_type"
        unique_together = (("app_label", "model"),)


class DjangoMigrations(models.Model):
    id = models.BigAutoField(primary_key=True)
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "django_migrations"


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "django_session"


class RegistersellDetail(models.Model):
    idsell = models.AutoField(primary_key=True)
    date = models.DateTimeField(auto_now=True)
    id_employed = models.CharField(max_length=150)
    total_sell = models.DecimalField(max_digits=10, decimal_places=2)
    type_pay = models.CharField(max_length=150)
    state_sell = models.CharField(max_length=150)
    notes = models.TextField(max_length=200, blank=True, null=True)
    quantity_pay = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    detail_sell = models.TextField()
    
    class Meta:
        verbose_name = "Register_sell"
        verbose_name_plural = "Register_sells"
        db_table = "register_sells"
        ordering = ["-date"]

    def __str__(self):
        return self.id_employed


class Clients(models.Model):
    name = models.CharField(max_length=200)
    email= models.EmailField(max_length=150, null=False, unique=True, default="no-email@example.com")
    direction = models.CharField(max_length=100)
    telephone = PhoneNumberField(blank=True, null=True, unique=True)
    nit = models.CharField(max_length=100)  
    country = models.CharField(max_length=100)  
    departament = models.CharField(max_length=100)  
    city = models.CharField(max_length=100)  

    class Meta:
        verbose_name = "Client"
        verbose_name_plural = "Clients"
        db_table = "clients"

    def __str__(self):
        return self.name
