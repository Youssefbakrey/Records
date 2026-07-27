#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import dns.resolver
import dns.exception
import sys
import os
from typing import Dict, List, Optional
from datetime import datetime
from collections import defaultdict

# ============================================
# الألوان للشكل الحلو في التيرمينال
# ============================================
class Colors:
    """ألوان التيرمينال"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'
    DIM = '\033[2m'
    
    ICON_DOMAIN = "🌐"
    ICON_SUCCESS = "✅"
    ICON_ERROR = "❌"
    ICON_WARNING = "⚠️"
    ICON_INFO = "📌"
    ICON_RECORD = "🔹"
    ICON_STATS = "📊"
    ICON_FILE = "📁"

# ============================================
# دالة جلب السجلات
# ============================================
def get_dns_records(domain: str, record_types: Optional[List[str]] = None) -> Dict[str, List[str]]:
    """
    جلب سجلات DNS لـ domain معين
    """
    if record_types is None:
        record_types = ['A', 'AAAA', 'CNAME', 'MX', 'TXT', 'NS', 'SOA', 'PTR']
    
    records = {}
    resolver = dns.resolver.Resolver()
    resolver.nameservers = ['8.8.8.8', '1.1.1.1']
    resolver.timeout = 3
    resolver.lifetime = 5
    
    for record_type in record_types:
        try:
            answers = resolver.resolve(domain, record_type)
            if answers:
                records[record_type] = [str(rdata).rstrip('.') for rdata in answers]
        except dns.resolver.NoAnswer:
            continue
        except dns.resolver.NXDOMAIN:
            return {'ERROR': 'Domain does not exist'}
        except dns.exception.Timeout:
            return {'ERROR': 'DNS query timed out'}
        except Exception as e:
            return {'ERROR': str(e)}
    
    return records

# ============================================
# دالة عرض النتائج بشكل منظم
# ============================================
def print_pretty_results(subdomain: str, records: Dict[str, List[str]], index: int, total: int):
    """
    عرض النتائج بشكل منظم وجميل
    """
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'─' * 60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}▶ {Colors.ICON_DOMAIN} [{index}/{total}] {Colors.UNDERLINE}{subdomain}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'─' * 60}{Colors.END}")
    
    if 'ERROR' in records:
        print(f"{Colors.RED}  {Colors.ICON_ERROR} خطأ: {records['ERROR']}{Colors.END}")
        return
    
    if not records:
        print(f"{Colors.YELLOW}  {Colors.ICON_WARNING} مفيش سجلات DNS موجودة{Colors.END}")
        return
    
    for record_type, values in records.items():
        icon = get_record_icon(record_type)
        color = get_record_color(record_type)
        
        print(f"  {Colors.BOLD}{color}{icon} {record_type}{Colors.END}")
        for idx, value in enumerate(values, 1):
            if len(values) > 1:
                prefix = f"    {Colors.DIM}{idx}.{Colors.END}"
            else:
                prefix = "    "
            formatted_value = format_record_value(record_type, value)
            print(f"{prefix} {Colors.GREEN}{formatted_value}{Colors.END}")

def get_record_icon(record_type: str) -> str:
    """أيقونة لكل نوع سجل"""
    icons = {
        'A': '🌍',
        'AAAA': '🌎',
        'CNAME': '🔗',
        'MX': '📧',
        'TXT': '📝',
        'NS': '🌐',
        'SOA': '⚙️',
        'PTR': '🔄',
        'SRV': '🖥️',
        'CAA': '🔐'
    }
    return icons.get(record_type, '📌')

def get_record_color(record_type: str) -> str:
    """لون لكل نوع سجل"""
    colors = {
        'A': Colors.GREEN,
        'AAAA': Colors.CYAN,
        'CNAME': Colors.YELLOW,
        'MX': Colors.BLUE,
        'TXT': Colors.HEADER,
        'NS': Colors.BOLD,
        'SOA': Colors.DIM,
        'PTR': Colors.GREEN
    }
    return colors.get(record_type, Colors.END)

def format_record_value(record_type: str, value: str) -> str:
    """تنسيق القيم حسب النوع"""
    if record_type == 'TXT':
        return f'"{value}"'
    elif record_type in ['MX', 'SRV']:
        return value.replace(' ', '  ')
    else:
        return value

# ============================================
# دالة عرض الإحصائيات
# ============================================
def print_statistics(results: Dict[str, Dict[str, List[str]]], total: int, output_file: str = None):
    """
    عرض إحصائيات مفصلة
    """
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'=' * 60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.ICON_STATS}  الإحصائيات النهائية{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'=' * 60}{Colors.END}")
    
    successful = sum(1 for r in results.values() if 'ERROR' not in r and r)
    failed = sum(1 for r in results.values() if 'ERROR' in r)
    empty = sum(1 for r in results.values() if not r)
    
    record_counts = defaultdict(int)
    for records in results.values():
        if 'ERROR' not in records and records:
            for record_type in records.keys():
                record_counts[record_type] += 1
    
    print(f"\n{Colors.BOLD}📦 المجموع الكلي:{Colors.END} {total}")
    print(f"{Colors.GREEN}✅ ناجح:{Colors.END} {successful}")
    print(f"{Colors.RED}❌ فشل:{Colors.END} {failed}")
    print(f"{Colors.YELLOW}⚠️  فاضي:{Colors.END} {empty}")
    
    success_rate = (successful / total * 100) if total > 0 else 0
    print(f"\n{Colors.BOLD}📈 نسبة النجاح:{Colors.END} {success_rate:.1f}%")
    
    if record_counts:
        print(f"\n{Colors.BOLD}📋 أنواع السجلات الموجودة:{Colors.END}")
        sorted_records = sorted(record_counts.items(), key=lambda x: x[1], reverse=True)
        for record_type, count in sorted_records:
            icon = get_record_icon(record_type)
            color = get_record_color(record_type)
            bar_length = int(count / max(record_counts.values()) * 20) if max(record_counts.values()) > 0 else 0
            bar = '█' * bar_length + '░' * (20 - bar_length)
            print(f"  {color}{icon} {record_type:<6}{Colors.END} {count:>3} domains  {Colors.CYAN}{bar}{Colors.END}")
    
    print(f"\n{Colors.DIM}⏱️  تم الفحص في: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.END}")
    
    if output_file:
        print(f"{Colors.ICON_FILE} 📁 النتائج محفوظة في: {Colors.UNDERLINE}{output_file}{Colors.END}")
    
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'=' * 60}{Colors.END}")

# ============================================
# 🔥 الدالة الجديدة: تجميع السجلات حسب النوع
# ============================================
def print_grouped_records(results: Dict[str, Dict[str, List[str]]]):
    """
    عرض كل السجلات مجمعة حسب النوع - عشان تاخدها كوبي مرة واحدة
    """
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'=' * 60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.HEADER}📋  جميع السجلات مجمعة حسب النوع{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'=' * 60}{Colors.END}")
    print(f"{Colors.DIM}💡 انسخ القسم اللي تحتاجه مباشرة{Colors.END}\n")
    
    # تجميع كل السجلات حسب النوع
    grouped_records = defaultdict(set)  # استخدام set عشان نمنع التكرار
    
    for domain, records in results.items():
        if 'ERROR' not in records and records:
            for record_type, values in records.items():
                for value in values:
                    grouped_records[record_type].add(value)
    
    # ترتيب الأنواع
    record_order = ['A', 'AAAA', 'CNAME', 'MX', 'TXT', 'NS', 'SOA', 'PTR', 'SRV', 'CAA']
    
    for record_type in record_order:
        if record_type in grouped_records:
            values = sorted(grouped_records[record_type])
            icon = get_record_icon(record_type)
            color = get_record_color(record_type)
            
            print(f"{Colors.BOLD}{color}{icon} {record_type} ({len(values)} record(s)){Colors.END}")
            print(f"{Colors.DIM}{'─' * 50}{Colors.END}")
            
            for idx, value in enumerate(values, 1):
                # تنسيق خاص للـ TXT
                if record_type == 'TXT':
                    display_value = f'"{value}"'
                else:
                    display_value = value
                print(f"  {Colors.GREEN}{idx:>3}. {display_value}{Colors.END}")
            
            print()  # سطر فاصل بين الأنواع
    
    print(f"{Colors.BOLD}{Colors.CYAN}{'=' * 60}{Colors.END}")

# ============================================
# دالة حفظ النتائج المجمعة في ملف
# ============================================
def save_grouped_records(results: Dict[str, Dict[str, List[str]]], output_file: str):
    """
    حفظ السجلات مجمعة حسب النوع في ملف منفصل
    """
    # استخراج اسم الملف الأساسي
    base_name = os.path.splitext(output_file)[0]
    grouped_file = f"{base_name}_grouped.txt"
    
    grouped_records = defaultdict(set)
    
    for domain, records in results.items():
        if 'ERROR' not in records and records:
            for record_type, values in records.items():
                for value in values:
                    grouped_records[record_type].add(value)
    
    with open(grouped_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("جميع السجلات مجمعة حسب النوع\n")
        f.write(f"تم التجميع في: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 80 + "\n")
        f.write("💡 انسخ القسم اللي تحتاجه مباشرة\n\n")
        
        record_order = ['A', 'AAAA', 'CNAME', 'MX', 'TXT', 'NS', 'SOA', 'PTR', 'SRV', 'CAA']
        
        for record_type in record_order:
            if record_type in grouped_records:
                values = sorted(grouped_records[record_type])
                f.write(f"\n{record_type} ({len(values)} record(s))\n")
                f.write("-" * 50 + "\n")
                for idx, value in enumerate(values, 1):
                    if record_type == 'TXT':
                        f.write(f'  {idx:>3}. "{value}"\n')
                    else:
                        f.write(f"  {idx:>3}. {value}\n")
                f.write("\n")
        
        # إضافة إحصائيات سريعة
        f.write("\n" + "=" * 80 + "\n")
        f.write("📊 إحصائيات التجميع\n")
        f.write("=" * 80 + "\n")
        total_records = sum(len(v) for v in grouped_records.values())
        f.write(f"📦 إجمالي السجلات الفريدة: {total_records}\n")
        f.write(f"📋 أنواع السجلات: {len(grouped_records)}\n")
        for record_type, values in grouped_records.items():
            f.write(f"  - {record_type}: {len(values)} record(s)\n")
    
    return grouped_file

# ============================================
# الدالة الأساسية
# ============================================
def process_subdomains(subdomains_file: str, output_file: Optional[str] = None,
                       record_types: Optional[List[str]] = None, verbose: bool = True):
    """
    معالجة subdomains وعرض النتائج بشكل منظم
    """
    try:
        with open(subdomains_file, 'r', encoding='utf-8') as f:
            subdomains = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"{Colors.RED}{Colors.ICON_ERROR} الملف {subdomains_file} مش موجود!{Colors.END}")
        return
    
    results = {}
    total = len(subdomains)
    
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'=' * 60}{Colors.END}")
    print(f"{Colors.BOLD}🚀  فحص Subdomains{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'=' * 60}{Colors.END}")
    print(f"{Colors.ICON_FILE} 📁 ملف الإدخال: {Colors.UNDERLINE}{subdomains_file}{Colors.END}")
    print(f"{Colors.ICON_STATS} 📦 عدد الـ subdomains: {total}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'=' * 60}{Colors.END}")
    print()
    
    for idx, subdomain in enumerate(subdomains, 1):
        if verbose:
            progress = int(idx / total * 40)
            bar = '█' * progress + '░' * (40 - progress)
            print(f"{Colors.DIM}⏳ التقدم: [{bar}] {idx}/{total}{Colors.END}", end='\r')
        
        records = get_dns_records(subdomain, record_types)
        results[subdomain] = records
        
        if verbose:
            print(f"{' ' * 60}", end='\r')
            print_pretty_results(subdomain, records, idx, total)
    
    # عرض الإحصائيات
    print_statistics(results, total, output_file)
    
    # 🔥 عرض السجلات المجمعة (الجزء الجديد)
    print_grouped_records(results)
    
    # حفظ النتائج
    if output_file:
        save_results_to_file(results, output_file)
        print(f"\n{Colors.GREEN}{Colors.ICON_SUCCESS} تم حفظ النتائج التفصيلية في: {Colors.UNDERLINE}{output_file}{Colors.END}")
        
        # حفظ السجلات المجمعة
        grouped_file = save_grouped_records(results, output_file)
        print(f"{Colors.GREEN}{Colors.ICON_SUCCESS} تم حفظ السجلات المجمعة في: {Colors.UNDERLINE}{grouped_file}{Colors.END}")
        print(f"{Colors.DIM}💡 افتح الملف وانسخ القسم اللي تحتاجه{Colors.END}")

# ============================================
# حفظ النتائج التفصيلية في ملف
# ============================================
def save_results_to_file(results: Dict, output_file: str):
    """
    حفظ النتائج في ملف منظم
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write(f"نتائج فحص DNS Records\n")
        f.write(f"تم الفحص في: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 80 + "\n\n")
        
        for subdomain, records in results.items():
            f.write(f"🌐 {subdomain}\n")
            f.write("-" * 50 + "\n")
            
            if 'ERROR' in records:
                f.write(f"❌ خطأ: {records['ERROR']}\n")
            elif not records:
                f.write("⚠️ مفيش سجلات موجودة\n")
            else:
                for record_type, values in records.items():
                    f.write(f"  {record_type}:\n")
                    for value in values:
                        if record_type == 'TXT':
                            f.write(f"    - \"{value}\"\n")
                        else:
                            f.write(f"    - {value}\n")
                    f.write("\n")
            f.write("\n")
        
        f.write("\n" + "=" * 80 + "\n")
        f.write("الإحصائيات\n")
        f.write("=" * 80 + "\n")
        
        successful = sum(1 for r in results.values() if 'ERROR' not in r and r)
        failed = sum(1 for r in results.values() if 'ERROR' in r)
        empty = sum(1 for r in results.values() if not r)
        
        f.write(f"✅ ناجح: {successful}\n")
        f.write(f"❌ فشل: {failed}\n")
        f.write(f"⚠️ فاضي: {empty}\n")
        f.write(f"📦 المجموع: {len(results)}\n")

# ============================================
# الدالة الرئيسية
# ============================================
def main():
    """الدالة الرئيسية"""
    
    record_types = ['A', 'AAAA', 'CNAME', 'MX', 'TXT', 'NS']
    
    if len(sys.argv) >= 2:
        input_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) >= 3 else 'dns_results.txt'
    else:
        input_file = 'subdomains.txt'
        output_file = 'dns_results.txt'
    
    if not os.path.exists(input_file):
        print(f"{Colors.YELLOW}{Colors.ICON_WARNING} ملف {input_file} مش موجود، بنعمل ملف مثال...{Colors.END}")
        with open(input_file, 'w', encoding='utf-8') as f:
            f.write("example.com\n")
            f.write("google.com\n")
            f.write("github.com\n")
            f.write("yahoo.com\n")
            f.write("microsoft.com\n")
        print(f"{Colors.GREEN}{Colors.ICON_SUCCESS} تم إنشاء {input_file} بمثاليات{Colors.END}\n")
    
    process_subdomains(
        subdomains_file=input_file,
        output_file=output_file,
        record_types=record_types,
        verbose=True
    )

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}{Colors.ICON_WARNING} تم إيقاف الفحص بواسطتك{Colors.END}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Colors.RED}{Colors.ICON_ERROR} خطأ غير متوقع: {e}{Colors.END}")
        sys.exit(1)
