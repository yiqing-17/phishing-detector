"""Build the result records shared by Gmail scans and pasted messages."""

from analysis import gen_ir, ir_download_fields


def build_analyzed_entry(sender, subject, body, report, html_score, rule_score, spam_prob):
    entry = {
        'level': report['risk_level'],
        'risk_score': report['risk_score'],
        'subject': subject[:55],
        'sender': sender[:60],
        'body': body[:4000],
        'explanation': report.get('explanation', '')[:200],
        'action': report.get('recommended_action', '')[:120],
        'tags': report.get('suspicious_points', [])[:5],
        'scores': [
            ['規則引擎', f'{rule_score}分'],
            ['ML 機率', f'{spam_prob:.1%}'],
            ['HTML', f'+{html_score}分'],
        ],
        'layers': report.get('analysis_layers', {}),
        'fusion_formula': report.get('fusion_formula', ''),
        'risk_breakdown': report.get('risk_breakdown', {}),
        'explainable_findings': report.get('explainable_findings', []),
        'safety_actions': report.get('safety_actions', []),
        'category': report.get('category', ''),
        'ir': None,
    }

    if report['risk_level'] == 'high':
        incident_id, incident = gen_ir({'sender': sender, 'subject': subject}, report)
        entry['ir'] = {
            'id': incident_id,
            'severity': incident.get('severity', 'High'),
            'impact': incident.get('impact_assessment', '')[:150],
            'actions': incident.get('immediate_actions', [])[:3],
            'status': incident.get('status', 'Open'),
            'risk_score': incident.get('risk_score', report.get('risk_score', 0)),
            'created_at': incident.get('created_at', ''),
            'containment': incident.get('containment', ''),
            'verification': incident.get('verification', ''),
            'recovery': incident.get('recovery', ''),
            **ir_download_fields(incident, sender, subject),
        }

    return entry
