"""
Email Service for Site Orders
Handles all email notifications throughout the order lifecycle.
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from jinja2 import Environment, BaseLoader

# Email configuration (from SystemConfig in production)
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
FROM_EMAIL = os.getenv("FROM_EMAIL", "team@innexar.com")
FROM_NAME = os.getenv("FROM_NAME", "Innexar")


class EmailService:
    """Handles sending transactional emails for site orders."""

    def __init__(self, smtp_host: str = None, smtp_port: int = None,
                 smtp_user: str = None, smtp_password: str = None,
                 from_email: str = None, from_name: str = None):
        self.smtp_host = smtp_host or SMTP_HOST
        self.smtp_port = smtp_port or SMTP_PORT
        self.smtp_user = smtp_user or SMTP_USER
        self.smtp_password = smtp_password or SMTP_PASSWORD
        self.from_email = from_email or FROM_EMAIL
        self.from_name = from_name or FROM_NAME
        self.jinja_env = Environment(loader=BaseLoader())

    def send_email(self, to_email: str, subject: str, html_content: str,
                   text_content: Optional[str] = None) -> bool:
        """Send an email using SMTP."""
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = to_email

            # Plain text version (fallback)
            if text_content:
                msg.attach(MIMEText(text_content, "plain"))

            # HTML version (primary)
            msg.attach(MIMEText(html_content, "html"))

            # Send via SMTP
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                if self.smtp_user and self.smtp_password:
                    server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            return True
        except Exception as e:
            print(f"Failed to send email: {e}")
            return False

    def render_template(self, template_str: str, context: dict) -> str:
        """Render a Jinja2 template string with context."""
        template = self.jinja_env.from_string(template_str)
        return template.render(**context)

    # ========== ORDER LIFECYCLE EMAILS ==========

    def send_payment_confirmation(self, order: dict) -> bool:
        """Send email when payment is received."""
        context = {
            "customer_name": order.get("customer_name", ""),
            "order_id": order.get("id"),
            "total_price": order.get("total_price", 399),
            "onboarding_url": f"https://innexar.com/launch/onboarding?order_id={order.get('id')}",
            "dashboard_url": f"https://innexar.com/launch/dashboard?order_id={order.get('id')}&email={order.get('customer_email', '')}",
        }

        html = self.render_template(PAYMENT_CONFIRMATION_TEMPLATE, context)
        return self.send_email(
            to_email=order.get("customer_email", ""),
            subject="🎉 Payment Confirmed - Let's Build Your Website!",
            html_content=html,
        )

    def send_onboarding_complete(self, order: dict) -> bool:
        """Send email when onboarding is completed."""
        business_name = order.get("onboarding", {}).get("business_name", order.get("customer_name", ""))
        context = {
            "customer_name": order.get("customer_name", ""),
            "business_name": business_name,
            "order_id": order.get("id"),
            "dashboard_url": f"https://innexar.com/launch/dashboard?order_id={order.get('id')}&email={order.get('customer_email', '')}",
        }

        html = self.render_template(ONBOARDING_COMPLETE_TEMPLATE, context)
        return self.send_email(
            to_email=order.get("customer_email", ""),
            subject=f"✅ Onboarding Complete - {business_name}'s Website is Now in Development!",
            html_content=html,
        )

    def send_site_in_progress(self, order: dict) -> bool:
        """Send email when site enters 'building' status."""
        business_name = order.get("onboarding", {}).get("business_name", order.get("customer_name", ""))
        context = {
            "customer_name": order.get("customer_name", ""),
            "business_name": business_name,
            "order_id": order.get("id"),
            "dashboard_url": f"https://innexar.com/launch/dashboard?order_id={order.get('id')}&email={order.get('customer_email', '')}",
        }

        html = self.render_template(SITE_IN_PROGRESS_TEMPLATE, context)
        return self.send_email(
            to_email=order.get("customer_email", ""),
            subject=f"🚀 We're Building {business_name}'s Website!",
            html_content=html,
        )

    def send_ready_for_review(self, order: dict, preview_url: str) -> bool:
        """Send email when site is ready for customer review."""
        business_name = order.get("onboarding", {}).get("business_name", order.get("customer_name", ""))
        context = {
            "customer_name": order.get("customer_name", ""),
            "business_name": business_name,
            "order_id": order.get("id"),
            "preview_url": preview_url,
            "dashboard_url": f"https://innexar.com/launch/dashboard?order_id={order.get('id')}&email={order.get('customer_email', '')}",
            "revisions_remaining": order.get("revisions_included", 2) - order.get("revisions_used", 0),
        }

        html = self.render_template(READY_FOR_REVIEW_TEMPLATE, context)
        return self.send_email(
            to_email=order.get("customer_email", ""),
            subject=f"👀 Your Website Preview is Ready - {business_name}",
            html_content=html,
        )

    def send_site_delivered(self, order: dict, site_url: str) -> bool:
        """Send email when site is delivered."""
        business_name = order.get("onboarding", {}).get("business_name", order.get("customer_name", ""))
        context = {
            "customer_name": order.get("customer_name", ""),
            "business_name": business_name,
            "order_id": order.get("id"),
            "site_url": site_url,
            "dashboard_url": f"https://innexar.com/launch/dashboard?order_id={order.get('id')}&email={order.get('customer_email', '')}",
        }

        html = self.render_template(SITE_DELIVERED_TEMPLATE, context)
        return self.send_email(
            to_email=order.get("customer_email", ""),
            subject=f"🎊 Congratulations! {business_name}'s Website is Live!",
            html_content=html,
        )

    def send_custom_email(self, to_email: str, subject: str, template_data: dict, template_name: str) -> bool:
        """Send a custom email with template name lookup."""
        templates = {
            "verification": VERIFICATION_TEMPLATE,
        }
        
        template_str = templates.get(template_name)
        if not template_str:
            print(f"Unknown template: {template_name}")
            return False
        
        html = self.render_template(template_str, template_data)
        return self.send_email(to_email=to_email, subject=subject, html_content=html)


# ========== EMAIL TEMPLATES ==========

BASE_STYLES = """
<style>
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; margin: 0; padding: 0; background: #0f172a; }
    .container { max-width: 600px; margin: 0 auto; background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); }
    .header { background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%); padding: 40px 30px; text-align: center; }
    .header h1 { color: white; margin: 0; font-size: 28px; font-weight: 700; }
    .header p { color: rgba(255,255,255,0.9); margin: 10px 0 0; font-size: 16px; }
    .content { padding: 40px 30px; color: #e2e8f0; }
    .content h2 { color: white; margin: 0 0 20px; font-size: 24px; }
    .content p { line-height: 1.7; margin: 0 0 20px; color: #94a3b8; }
    .button { display: inline-block; background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); color: white !important; padding: 16px 32px; text-decoration: none; border-radius: 12px; font-weight: 600; font-size: 16px; margin: 10px 0; }
    .button:hover { background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%); }
    .button-secondary { background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); }
    .card { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 16px; padding: 24px; margin: 20px 0; }
    .card h3 { color: white; margin: 0 0 15px; font-size: 18px; }
    .card ul { margin: 0; padding: 0; list-style: none; }
    .card li { padding: 8px 0; color: #94a3b8; display: flex; align-items: center; gap: 10px; }
    .card li::before { content: "✓"; color: #22c55e; font-weight: bold; }
    .highlight { color: #3b82f6; font-weight: 600; }
    .success-badge { background: rgba(34,197,94,0.2); border: 1px solid rgba(34,197,94,0.3); color: #22c55e; padding: 8px 16px; border-radius: 8px; display: inline-block; font-weight: 600; }
    .footer { padding: 30px; text-align: center; border-top: 1px solid rgba(255,255,255,0.1); }
    .footer p { color: #64748b; font-size: 14px; margin: 5px 0; }
    .footer a { color: #3b82f6; text-decoration: none; }
    .divider { height: 1px; background: rgba(255,255,255,0.1); margin: 30px 0; }
    .icon-circle { width: 80px; height: 80px; background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%); border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 20px; font-size: 36px; }
    .timeline { margin: 20px 0; }
    .timeline-item { display: flex; gap: 15px; margin: 15px 0; }
    .timeline-dot { width: 12px; height: 12px; background: #3b82f6; border-radius: 50%; margin-top: 5px; flex-shrink: 0; }
    .timeline-dot.done { background: #22c55e; }
    .timeline-dot.pending { background: #64748b; }
    .timeline-content { flex: 1; }
    .timeline-content h4 { color: white; margin: 0 0 5px; font-size: 16px; }
    .timeline-content p { margin: 0; color: #64748b; font-size: 14px; }
</style>
"""

PAYMENT_CONFIRMATION_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    """ + BASE_STYLES + """
</head>
<body>
<div class="container">
    <div class="header">
        <h1>Payment Confirmed! 🎉</h1>
        <p>Your professional website journey begins now</p>
    </div>
    <div class="content">
        <div style="text-align: center;">
            <div class="icon-circle">✓</div>
            <span class="success-badge">Order #{{ order_id }} Confirmed</span>
        </div>

        <div class="divider"></div>

        <h2>Hello {{ customer_name }}!</h2>
        <p>Thank you for choosing Innexar! We've received your payment of <span class="highlight">${{ total_price }}</span> and we're excited to start building your new website.</p>

        <div class="card">
            <h3>What's Next?</h3>
            <ul>
                <li>Complete your onboarding form (takes ~5 minutes)</li>
                <li>Our design team reviews your requirements</li>
                <li>First draft delivered in 3-5 business days</li>
                <li>2 rounds of revisions included</li>
            </ul>
        </div>

        <div style="text-align: center;">
            <a href="{{ onboarding_url }}" class="button">Complete Onboarding →</a>
            <br><br>
            <a href="{{ dashboard_url }}" class="button button-secondary">Track Your Project</a>
        </div>

        <div class="divider"></div>

        <p style="text-align: center; color: #64748b; font-size: 14px;">
            Questions? Reply to this email or reach us at support@innexar.com
        </p>
    </div>
    <div class="footer">
        <p>© 2026 Innexar. Building beautiful websites for local businesses.</p>
        <p><a href="https://innexar.com">innexar.com</a></p>
    </div>
</div>
</body>
</html>
"""

ONBOARDING_COMPLETE_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    """ + BASE_STYLES + """
</head>
<body>
<div class="container">
    <div class="header" style="background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);">
        <h1>Onboarding Complete! ✅</h1>
        <p>{{ business_name }}'s website is now in the queue</p>
    </div>
    <div class="content">
        <div style="text-align: center;">
            <div class="icon-circle">🚀</div>
        </div>

        <h2>Great news, {{ customer_name }}!</h2>
        <p>We've received all the information we need to start building <span class="highlight">{{ business_name }}</span>'s website. Our design team is now reviewing your requirements.</p>

        <div class="card">
            <h3>Project Timeline</h3>
            <div class="timeline">
                <div class="timeline-item">
                    <div class="timeline-dot done"></div>
                    <div class="timeline-content">
                        <h4>Order Confirmed</h4>
                        <p>Payment received & onboarding complete</p>
                    </div>
                </div>
                <div class="timeline-item">
                    <div class="timeline-dot" style="background: #3b82f6; box-shadow: 0 0 0 4px rgba(59,130,246,0.3);"></div>
                    <div class="timeline-content">
                        <h4>Design & Development</h4>
                        <p>Our team is crafting your website (3-5 days)</p>
                    </div>
                </div>
                <div class="timeline-item">
                    <div class="timeline-dot pending"></div>
                    <div class="timeline-content">
                        <h4>Review & Revisions</h4>
                        <p>Preview and request changes</p>
                    </div>
                </div>
                <div class="timeline-item">
                    <div class="timeline-dot pending"></div>
                    <div class="timeline-content">
                        <h4>Launch</h4>
                        <p>Your website goes live!</p>
                    </div>
                </div>
            </div>
        </div>

        <div style="text-align: center;">
            <a href="{{ dashboard_url }}" class="button">Track Your Project →</a>
        </div>

        <div class="divider"></div>

        <p style="text-align: center; color: #64748b; font-size: 14px;">
            We'll notify you as soon as your site preview is ready for review.
        </p>
    </div>
    <div class="footer">
        <p>© 2026 Innexar. Building beautiful websites for local businesses.</p>
    </div>
</div>
</body>
</html>
"""

SITE_IN_PROGRESS_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    """ + BASE_STYLES + """
</head>
<body>
<div class="container">
    <div class="header" style="background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%);">
        <h1>Your Site is Being Built! 🛠️</h1>
        <p>Our designers are working their magic</p>
    </div>
    <div class="content">
        <h2>Exciting update, {{ customer_name }}!</h2>
        <p>Our design team has started working on <span class="highlight">{{ business_name }}</span>'s website. We're carefully crafting every detail to match your vision.</p>

        <div class="card">
            <h3>What We're Working On</h3>
            <ul>
                <li>Custom layout based on your preferences</li>
                <li>Mobile-responsive design</li>
                <li>SEO optimization for local search</li>
                <li>Your brand colors and style</li>
                <li>Contact forms and call-to-action buttons</li>
            </ul>
        </div>

        <p>We'll send you an email as soon as the first draft is ready for your review. This typically takes <span class="highlight">3-5 business days</span>.</p>

        <div style="text-align: center;">
            <a href="{{ dashboard_url }}" class="button">Track Progress →</a>
        </div>
    </div>
    <div class="footer">
        <p>© 2026 Innexar. Building beautiful websites for local businesses.</p>
    </div>
</div>
</body>
</html>
"""

READY_FOR_REVIEW_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    """ + BASE_STYLES + """
</head>
<body>
<div class="container">
    <div class="header" style="background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);">
        <h1>Your Site Preview is Ready! 👀</h1>
        <p>Time to see your new website</p>
    </div>
    <div class="content">
        <div style="text-align: center;">
            <div class="icon-circle" style="background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);">👁️</div>
        </div>

        <h2>Great news, {{ customer_name }}!</h2>
        <p>Your <span class="highlight">{{ business_name }}</span> website is ready for review! Take a look and let us know what you think.</p>

        <div style="text-align: center; margin: 30px 0;">
            <a href="{{ preview_url }}" class="button" style="font-size: 18px; padding: 20px 40px;">View Your Website →</a>
        </div>

        <div class="card">
            <h3>Review Instructions</h3>
            <ul>
                <li>Check all pages on desktop and mobile</li>
                <li>Verify your contact information is correct</li>
                <li>Review the colors, fonts, and images</li>
                <li>Test the contact form</li>
            </ul>
        </div>

        <div class="card" style="border-color: rgba(59,130,246,0.5);">
            <h3 style="color: #3b82f6;">Revisions Available</h3>
            <p style="margin: 0;">You have <span class="highlight">{{ revisions_remaining }} revision(s)</span> remaining. Reply to this email with any changes you'd like us to make.</p>
        </div>

        <div style="text-align: center;">
            <a href="{{ dashboard_url }}" class="button button-secondary">View Project Dashboard</a>
        </div>
    </div>
    <div class="footer">
        <p>© 2026 Innexar. Building beautiful websites for local businesses.</p>
    </div>
</div>
</body>
</html>
"""

SITE_DELIVERED_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    """ + BASE_STYLES + """
</head>
<body>
<div class="container">
    <div class="header" style="background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);">
        <h1>Congratulations! 🎊</h1>
        <p>{{ business_name }}'s website is now LIVE!</p>
    </div>
    <div class="content">
        <div style="text-align: center;">
            <div class="icon-circle" style="font-size: 48px;">🚀</div>
            <span class="success-badge" style="font-size: 18px; padding: 12px 24px;">Website Delivered!</span>
        </div>

        <div class="divider"></div>

        <h2>You did it, {{ customer_name }}!</h2>
        <p>Your professional website for <span class="highlight">{{ business_name }}</span> is now live and ready to impress your customers!</p>

        <div style="text-align: center; margin: 30px 0;">
            <a href="{{ site_url }}" class="button" style="font-size: 18px; padding: 20px 40px; background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);">Visit Your Website →</a>
        </div>

        <div class="card">
            <h3>What's Included</h3>
            <ul>
                <li>Full source code ownership</li>
                <li>30 days of post-launch support</li>
                <li>Mobile-responsive design</li>
                <li>SEO-optimized pages</li>
                <li>Contact form integration</li>
            </ul>
        </div>

        <div class="card" style="border-color: rgba(34,197,94,0.5);">
            <h3 style="color: #22c55e;">🌟 Help Others Find Great Websites</h3>
            <p style="margin: 0;">Love your new site? Share your experience! Your review helps other business owners find us.</p>
        </div>

        <div class="divider"></div>

        <p style="text-align: center;">Thank you for trusting Innexar with your online presence. We're here if you need anything!</p>

        <div style="text-align: center;">
            <a href="{{ dashboard_url }}" class="button button-secondary">View Your Dashboard</a>
        </div>
    </div>
    <div class="footer">
        <p>© 2026 Innexar. Building beautiful websites for local businesses.</p>
        <p style="margin-top: 15px;">
            <a href="https://innexar.com">Website</a> &nbsp;|&nbsp;
            <a href="mailto:support@innexar.com">Support</a>
        </p>
    </div>
</div>
</body>
</html>
"""

VERIFICATION_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    """ + BASE_STYLES + """
</head>
<body>
<div class="container">
    <div class="header">
        <h1>Verifique seu Email ✉️</h1>
        <p>Acesse seu Portal de Cliente Innexar</p>
    </div>
    <div class="content">
        <div style="text-align: center;">
            <div class="icon-circle" style="background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);">🔐</div>
        </div>

        <h2>Olá {{ customer_name }}!</h2>
        <p>Seu site está sendo desenvolvido! Para acompanhar o progresso, verifique seu email clicando no botão abaixo.</p>

        <div class="card">
            <h3>🔑 Suas Credenciais de Acesso</h3>
            <p><strong>Email:</strong> O email que você usou para comprar</p>
            <p><strong>Senha Temporária:</strong> <code style="background: rgba(59,130,246,0.2); padding: 4px 12px; border-radius: 6px; font-family: monospace; color: #3b82f6;">{{ temp_password }}</code></p>
            <p style="font-size: 14px; color: #64748b; margin-top: 15px;">⚠️ Guarde esta senha! Você pode alterá-la após o login.</p>
        </div>

        <div style="text-align: center; margin: 30px 0;">
            <a href="{{ verification_url }}" class="button" style="font-size: 18px; padding: 18px 36px;">Verificar Email e Acessar →</a>
        </div>

        <div class="divider"></div>

        <p style="text-align: center; color: #64748b; font-size: 14px;">
            Se você não solicitou isso, ignore este email.
        </p>
    </div>
    <div class="footer">
        <p>© 2026 Innexar. Construindo sites profissionais para negócios locais.</p>
        <p><a href="https://innexar.app">innexar.app</a></p>
    </div>
</div>
</body>
</html>
"""


# Singleton instance
email_service = EmailService()

