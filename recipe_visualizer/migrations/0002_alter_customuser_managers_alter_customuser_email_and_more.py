# Generated by Django 4.2.5 on 2023-09-07 11:16

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('recipe_visualizer', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelManagers(
            name='customuser',
            managers=[
            ],
        ),
        migrations.AlterField(
            model_name='customuser',
            name='email',
            field=models.EmailField(max_length=254, unique=True),
        ),
        migrations.AlterField(
            model_name='feedback',
            name='recipe',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='feedback', to='recipe_visualizer.recipe'),
        ),
        migrations.AlterField(
            model_name='recipeingredient',
            name='recipe',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ingredients', to='recipe_visualizer.recipe'),
        ),
        migrations.AlterField(
            model_name='recipestep',
            name='recipe',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='steps', to='recipe_visualizer.recipe'),
        ),
        migrations.AlterField(
            model_name='recipetype',
            name='recipe',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='recipe_types', to='recipe_visualizer.recipe'),
        ),
        migrations.AlterField(
            model_name='stepimage',
            name='step',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='step_images', to='recipe_visualizer.recipestep'),
        ),
    ]
