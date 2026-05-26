from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ingestion', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='electricityrecord',
            name='account_no',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='electricityrecord',
            name='address',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='electricityrecord',
            name='bill_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='electricityrecord',
            name='bill_reference',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='electricityrecord',
            name='billing_days',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='electricityrecord',
            name='city',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='electricityrecord',
            name='consumption_unit',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='electricityrecord',
            name='contracted_demand_kva',
            field=models.DecimalField(blank=True, decimal_places=3, max_digits=14, null=True),
        ),
        migrations.AddField(
            model_name='electricityrecord',
            name='currency',
            field=models.CharField(blank=True, max_length=10),
        ),
        migrations.AddField(
            model_name='electricityrecord',
            name='demand_charge_inr',
            field=models.DecimalField(blank=True, decimal_places=3, max_digits=14, null=True),
        ),
        migrations.AddField(
            model_name='electricityrecord',
            name='demand_unit',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='electricityrecord',
            name='discom',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='electricityrecord',
            name='due_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='electricityrecord',
            name='electricity_duty_inr',
            field=models.DecimalField(blank=True, decimal_places=3, max_digits=14, null=True),
        ),
        migrations.AddField(
            model_name='electricityrecord',
            name='energy_charge_inr',
            field=models.DecimalField(blank=True, decimal_places=3, max_digits=14, null=True),
        ),
        migrations.AddField(
            model_name='electricityrecord',
            name='hv_lv',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='electricityrecord',
            name='max_demand',
            field=models.DecimalField(blank=True, decimal_places=3, max_digits=14, null=True),
        ),
        migrations.AddField(
            model_name='electricityrecord',
            name='meter_read_end',
            field=models.DecimalField(blank=True, decimal_places=3, max_digits=14, null=True),
        ),
        migrations.AddField(
            model_name='electricityrecord',
            name='meter_read_start',
            field=models.DecimalField(blank=True, decimal_places=3, max_digits=14, null=True),
        ),
        migrations.AddField(
            model_name='electricityrecord',
            name='offpeak_kwh',
            field=models.DecimalField(blank=True, decimal_places=3, max_digits=14, null=True),
        ),
        migrations.AddField(
            model_name='electricityrecord',
            name='payment_status',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name='electricityrecord',
            name='peak_kwh',
            field=models.DecimalField(blank=True, decimal_places=3, max_digits=14, null=True),
        ),
        migrations.AddField(
            model_name='electricityrecord',
            name='pf_penalty_inr',
            field=models.DecimalField(blank=True, decimal_places=3, max_digits=14, null=True),
        ),
        migrations.AddField(
            model_name='electricityrecord',
            name='power_factor',
            field=models.DecimalField(blank=True, decimal_places=3, max_digits=6, null=True),
        ),
        migrations.AddField(
            model_name='electricityrecord',
            name='read_type',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='electricityrecord',
            name='regulatory_charge_inr',
            field=models.DecimalField(blank=True, decimal_places=3, max_digits=14, null=True),
        ),
        migrations.AddField(
            model_name='electricityrecord',
            name='shoulder_kwh',
            field=models.DecimalField(blank=True, decimal_places=3, max_digits=14, null=True),
        ),
        migrations.AddField(
            model_name='electricityrecord',
            name='site_name',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='electricityrecord',
            name='source_payload',
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name='electricityrecord',
            name='state',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='electricityrecord',
            name='supply_charge_inr',
            field=models.DecimalField(blank=True, decimal_places=3, max_digits=14, null=True),
        ),
        migrations.AddField(
            model_name='electricityrecord',
            name='supply_voltage',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name='electricityrecord',
            name='tariff_category',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='electricityrecord',
            name='tariff_code',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='electricityrecord',
            name='total_bill_inr',
            field=models.DecimalField(blank=True, decimal_places=3, max_digits=14, null=True),
        ),
        migrations.AddField(
            model_name='fuelrecord',
            name='aedat',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='fuelrecord',
            name='aufnr',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name='fuelrecord',
            name='bedat',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='fuelrecord',
            name='bsart',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='fuelrecord',
            name='bstyp',
            field=models.CharField(blank=True, max_length=10),
        ),
        migrations.AddField(
            model_name='fuelrecord',
            name='budat',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='fuelrecord',
            name='bwart',
            field=models.CharField(blank=True, max_length=10),
        ),
        migrations.AddField(
            model_name='fuelrecord',
            name='ebeln',
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AddField(
            model_name='fuelrecord',
            name='ebelp',
            field=models.CharField(blank=True, max_length=10),
        ),
        migrations.AddField(
            model_name='fuelrecord',
            name='ekgrp',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='fuelrecord',
            name='ekorg',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='fuelrecord',
            name='inco1',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='fuelrecord',
            name='kostl',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name='fuelrecord',
            name='lgort',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name='fuelrecord',
            name='lifnr',
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AddField(
            model_name='fuelrecord',
            name='loekz',
            field=models.CharField(blank=True, max_length=10),
        ),
        migrations.AddField(
            model_name='fuelrecord',
            name='matkl',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name='fuelrecord',
            name='matnr',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='fuelrecord',
            name='mblnr',
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AddField(
            model_name='fuelrecord',
            name='mjahr',
            field=models.CharField(blank=True, max_length=10),
        ),
        migrations.AddField(
            model_name='fuelrecord',
            name='netpr',
            field=models.DecimalField(blank=True, decimal_places=3, max_digits=14, null=True),
        ),
        migrations.AddField(
            model_name='fuelrecord',
            name='netwr',
            field=models.DecimalField(blank=True, decimal_places=3, max_digits=14, null=True),
        ),
        migrations.AddField(
            model_name='fuelrecord',
            name='section_source',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='fuelrecord',
            name='source_payload',
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name='fuelrecord',
            name='statu',
            field=models.CharField(blank=True, max_length=10),
        ),
        migrations.AddField(
            model_name='fuelrecord',
            name='txz01',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='fuelrecord',
            name='vendor_name',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='fuelrecord',
            name='waers',
            field=models.CharField(blank=True, max_length=10),
        ),
        migrations.AddField(
            model_name='fuelrecord',
            name='werks',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='fuelrecord',
            name='wkurs',
            field=models.DecimalField(blank=True, decimal_places=4, max_digits=14, null=True),
        ),
        migrations.AddField(
            model_name='fuelrecord',
            name='zeile',
            field=models.CharField(blank=True, max_length=10),
        ),
        migrations.AddField(
            model_name='fuelrecord',
            name='zterms',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='travelrecord',
            name='airline_code',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='travelrecord',
            name='airline_name',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='travelrecord',
            name='amount',
            field=models.DecimalField(blank=True, decimal_places=3, max_digits=14, null=True),
        ),
        migrations.AddField(
            model_name='travelrecord',
            name='approval_status',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name='travelrecord',
            name='cabin_class',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name='travelrecord',
            name='check_in_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='travelrecord',
            name='check_out_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='travelrecord',
            name='cost_center',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='travelrecord',
            name='currency',
            field=models.CharField(blank=True, max_length=10),
        ),
        migrations.AddField(
            model_name='travelrecord',
            name='department',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='travelrecord',
            name='destination_city',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='travelrecord',
            name='destination_iata',
            field=models.CharField(blank=True, max_length=10),
        ),
        migrations.AddField(
            model_name='travelrecord',
            name='emission_factor',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=14, null=True),
        ),
        migrations.AddField(
            model_name='travelrecord',
            name='employee_id',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='travelrecord',
            name='employee_name',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='travelrecord',
            name='estimated_emissions_kgco2e',
            field=models.DecimalField(blank=True, decimal_places=3, max_digits=14, null=True),
        ),
        migrations.AddField(
            model_name='travelrecord',
            name='expense_type',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='travelrecord',
            name='flight_number',
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AddField(
            model_name='travelrecord',
            name='ground_transport_type',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='travelrecord',
            name='home_city',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='travelrecord',
            name='hotel_city',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='travelrecord',
            name='hotel_name',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='travelrecord',
            name='job_title',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='travelrecord',
            name='notes',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='travelrecord',
            name='origin_city',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='travelrecord',
            name='origin_iata',
            field=models.CharField(blank=True, max_length=10),
        ),
        migrations.AddField(
            model_name='travelrecord',
            name='payment_method',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='travelrecord',
            name='policy_compliant',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='travelrecord',
            name='policy_exception_reason',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='travelrecord',
            name='receipt_attached',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='travelrecord',
            name='reimbursable',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='travelrecord',
            name='report_id',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='travelrecord',
            name='source_payload',
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name='travelrecord',
            name='transaction_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='travelrecord',
            name='trip_purpose',
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
