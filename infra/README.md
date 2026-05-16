# Infrastructure as Code — Terraform

## Estructura de carpetas

```
infra/
├── modules/
│   └── crud/              ← Módulo reutilizable (QUÉ desplegar)
│       ├── main.tf        ←   DynamoDB tables, IAM roles, Lambda functions
│       ├── variables.tf   ←   Parámetros de entrada
│       └── outputs.tf     ←   Valores de salida (ARNs, nombres)
├── test/                  ← Entorno local (DÓNDE desplegar — local)
│   ├── main.tf            ←   Invoca module "crud" con stage=local
│   ├── providers.tf       ←   Provider AWS → Floci (localhost:4566)
│   ├── variables.tf       ←   Variables con defaults locales
│   └── terraform.tfvars   ←   Valores concretos para local
└── prod/                  ← Entorno producción (DÓNDE desplegar — AWS real)
    ├── main.tf            ←   Invoca module "crud" con stage=prod + auto-zip
    ├── providers.tf       ←   Provider AWS → AWS real (sin overrides)
    └── variables.tf       ←   Variables con defaults de producción
```

## ¿Para qué sirve cada carpeta?

### `modules/crud/` — El QUÉ (módulo reutilizable)

Define **qué recursos** se crean, sin decir **dónde**. Es una plantilla que se
reutiliza en cada entorno.

**Contiene:**
- 3 tablas DynamoDB (Dictionary, Product, ShoppingCart)
- IAM role + policy para Lambda (solo en prod)
- 3 Lambda functions (solo en prod)

**No sabe** si se despliega en Floci o en AWS real. Solo recibe variables.

### `test/` — Entorno local (Floci)

Despliega **solo DynamoDB** en Floci (`localhost:4566`).

**No crea Lambdas ni IAM** porque Floci no los soporta.

Se usa para:
- Desarrollo local
- Tests de integración contra DynamoDB local
- Validar que el código funciona antes de subir a AWS

### `prod/` — Entorno producción (AWS real)

Despliega **todo**: DynamoDB + IAM + Lambda functions en AWS real.

**Auto-genera los zips** de cada Lambda durante `terraform plan` — no hay que
crearlos manualmente.

## ¿Por qué usar módulos?

Sin módulos, tendrías que duplicar las 3 tablas, IAM, y Lambdas en `test/` y
`prod/`. Con un módulo:

| Sin módulos | Con módulos |
|-------------|-------------|
| Definir tablas en `test/` | Definir tablas **una vez** en `modules/crud/` |
| Definir tablas en `prod/` | Invocar módulo desde `test/` y `prod/` |
| Si cambias algo, editas 2 lugares | Si cambias algo, editas **1 lugar** |

El módulo es la **fuente de verdad** de qué recursos existen. Los entornos
(`test/`, `prod/`) solo dicen **con qué parámetros** invocarlo.

## Flujo de trabajo

### Local (desarrollo y tests)

```bash
# 1. Asegúrate de que Floci esté corriendo
docker-compose up -d

# 2. Desplegar infra local (solo DynamoDB)
terraform -chdir=infra/test init     # solo la primera vez
terraform -chdir=infra/test apply

# 3. Correr tests (usan las tablas creadas por Terraform)
python3 -m unittest discover -s backend/tests -v

# 4. Destruir infra cuando termines
terraform -chdir=infra/test destroy
```

### Producción (AWS real)

```bash
# 1. Configurar credenciales AWS
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."
export AWS_DEFAULT_REGION="us-east-1"

# 2. Desplegar infra en AWS (DynamoDB + IAM + Lambda)
terraform -chdir=infra/prod init     # solo la primera vez
terraform -chdir=infra/prod plan     # revisar cambios antes de aplicar
terraform -chdir=infra/prod apply

# 3. Los zips de Lambda se generan automáticamente durante plan/apply
#    No necesitas crearlos manualmente.
```

## ¿Cómo funciona el auto-zip de Lambda?

En `infra/prod/main.tf` hay `data "archive_file"` blocks que leen los archivos
Python del backend y generan zips **durante** `terraform plan`:

```hcl
data "archive_file" "dictionary" {
  type        = "zip"
  output_path = "${path.module}/.terraform/artifacts/dictionary.zip"

  source {
    content  = file("${local.backend_root}/handlers/dictionary_handler.py")
    filename = "backend/handlers/dictionary_handler.py"
  }
  # ... más archivos (DAL, __init__.py, etc.)
}
```

Cada Lambda incluye:
- Su handler específico
- El DAL compartido (`db_client.py`, `errors.py`, `*_dao.py`)
- Los `__init__.py` necesarios para imports de Python

Los zips se guardan en `infra/prod/.terraform/artifacts/` (gitignored).

## Stage-aware configuration

El módulo usa `var.stage` para decidir qué crear:

| Recurso | stage=local | stage=prod |
|---------|-------------|------------|
| DynamoDB tables | ✅ | ✅ |
| IAM role/policy | ❌ | ✅ |
| Lambda functions | ❌ | ✅ |

Esto se logra con `count = var.stage == "prod" ? 1 : 0` en los recursos
que solo aplican en producción.

## Variables principales

| Variable | Default (test) | Default (prod) | Descripción |
|----------|----------------|----------------|-------------|
| `stage` | `local` | `prod` | Entorno de despliegue |
| `aws_region` | `us-east-1` | `us-east-1` | Región AWS |
| `aws_endpoint_url` | `http://localhost:4566` | `""` | Override para Floci |

## Tablas DynamoDB

| Tabla | Partition Key | Atributos |
|-------|---------------|-----------|
| Dictionary | `Word` (S) | `definition` (S) |
| Product | `uuid` (S) | `name` (S), `price` (N) |
| ShoppingCart | `UUID` (S) | `product_ids` (List) |
