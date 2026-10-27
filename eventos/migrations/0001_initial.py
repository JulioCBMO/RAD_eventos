# Generated for the existing RAD event-registration project.
import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]
    operations = [
        migrations.CreateModel(
            name="Sala",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nome", models.CharField(max_length=100)),
                ("bloco", models.CharField(blank=True, max_length=50)),
                ("capacidade", models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1)])),
            ],
            options={"ordering": ["bloco", "nome"]},
        ),
        migrations.CreateModel(
            name="Evento",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nome", models.CharField(max_length=200)),
                ("descricao", models.TextField(blank=True)),
                ("data_inicio", models.DateTimeField()),
                ("data_fim", models.DateTimeField()),
                ("inscricoes_abertas", models.BooleanField(default=True)),
                ("organizador", models.ForeignKey(editable=False, on_delete=django.db.models.deletion.PROTECT, related_name="eventos_organizados", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["data_inicio"]},
        ),
        migrations.CreateModel(
            name="Atividade",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("titulo", models.CharField(max_length=200)),
                ("tipo", models.CharField(choices=[("PAL", "Palestra"), ("TRE", "Treinamento"), ("APR", "Apresentação")], max_length=3)),
                ("descricao", models.TextField(blank=True)),
                ("responsavel", models.CharField(max_length=150)),
                ("inicio", models.DateTimeField()),
                ("fim", models.DateTimeField()),
                ("evento", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="atividades", to="eventos.evento")),
                ("sala", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="atividades", to="eventos.sala")),
            ],
            options={"ordering": ["inicio"], "verbose_name_plural": "atividades"},
        ),
        migrations.CreateModel(
            name="InscricaoEvento",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("data", models.DateTimeField(auto_now_add=True)),
                ("evento", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="inscricoes", to="eventos.evento")),
                ("participante", models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name="inscricoes_evento", to=settings.AUTH_USER_MODEL)),
            ],
            options={"verbose_name": "inscrição no evento", "verbose_name_plural": "inscrições em eventos"},
        ),
        migrations.CreateModel(
            name="InscricaoAtividade",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("data", models.DateTimeField(auto_now_add=True)),
                ("atividade", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="inscricoes", to="eventos.atividade")),
                ("inscricao_evento", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="inscricoes_atividade", to="eventos.inscricaoevento")),
            ],
            options={"verbose_name": "inscrição na atividade", "verbose_name_plural": "inscrições em atividades"},
        ),
        migrations.AddConstraint(
            model_name="inscricaoevento",
            constraint=models.UniqueConstraint(fields=("evento", "participante"), name="unica_inscricao_por_evento"),
        ),
        migrations.AddConstraint(
            model_name="inscricaoatividade",
            constraint=models.UniqueConstraint(fields=("inscricao_evento", "atividade"), name="unica_inscricao_por_atividade"),
        ),
    ]
