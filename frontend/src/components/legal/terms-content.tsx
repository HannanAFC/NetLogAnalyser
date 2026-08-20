export function TermsContent( )
{
	return (
		<article className='prose-legal max-w-3xl'>
			<p className='text-sm text-text-secondary'>Last updated: 19th August, 2026</p>

			<p>
				These Terms & Conditions ('Terms') govern your use of
				NetLogAnalyser (the 'Service'), operated by
				NetLogAnalyser ('we', 'us'). By creating an account
				or using the Service, you agree to these Terms.
			</p>

			<h2>1. The Service</h2>
			<p>
				NetLogAnalyser lets you submit network packet metadata via an API
				key, stores and enriches it, and provides a dashboard and live
				feed for viewing it. The Service is currently provided free of
				charge.
			</p>

			<h2>2. Accounts</h2>
			<p>
				You must provide a valid email address and keep your login
				credentials confidential. You are responsible for all activity
				under your account and any API keys you generate, and must notify
				us promptly at support@netloganalyser.com of any suspected compromise.
			</p>

			<h2>3. Acceptable use - data you submit</h2>
			<p>By submitting network log data, you represent and warrant that:</p>
			<ul>
				<li>
					You are authorized to capture, process, and submit that data -
					e.g. it originates from your own network or systems you
					administer, or you have obtained proper consent/legal authority
					to monitor the traffic.
				</li>
				<li>
					Your capture and submission of the data complies with
					applicable law, including any wiretapping, interception, or
					data protection laws in your jurisdiction.
				</li>
				<li>
					You will not submit data captured from networks or devices you
					do not have the right to monitor.
				</li>
			</ul>
			<p>
				You are solely responsible for the network data you submit,
				including any personal data of third parties contained within it.
				We act as a processor of that data on your instructions.
			</p>
			<p>You also agree not to:</p>
			<ul>
				<li>Use the Service to store or transmit unlawful content</li>
				<li>Attempt to bypass rate limits or probe for vulnerabilities</li>
				<li>Share your account or API keys with unauthorized third parties</li>
				<li>Reverse engineer the Service beyond what applicable law permits</li>
			</ul>

			<h2>4. Service availability</h2>
			<p>
				The Service is provided free, 'as is' and 'as available', with no
				uptime guarantee or SLA. We may modify, suspend, or discontinue
				the Service at any time.
			</p>

			<h2>5. Data retention & deletion</h2>
			<p>
				See our Privacy Policy for retention periods. You may request
				deletion of your account and data at any time via
				support@netloganalyser.com.
			</p>

			<h2>6. Intellectual property</h2>
			<p>
				The Service's software, design, and branding are owned by
				NetLogAnalyser. You retain ownership of the network
				log data you submit, and grant us a limited license to store,
				process, and display it back to you.
			</p>

			<h2>7. Disclaimers</h2>
			<p>
				Anomaly scores are heuristic-based and may produce false
				positives or false negatives. The Service should not be relied
				upon as the sole basis for security-critical decisions. We make
				no warranty as to the accuracy of any output, including
				geo-location data.
			</p>

			<h2>8. Limitation of liability</h2>
			<p>
				To the maximum extent permitted by law, NetLogAnalyser
                is not liable for indirect, incidental, or consequential
				damages arising from your use of the Service. Nothing
                here excludes liability that cannot be excluded under
                applicable law.
			</p>

			<h2>9. Termination</h2>
			<p>
				You may stop using the Service and delete your account at any
				time. We may suspend or terminate access for breach of these
				Terms, in particular Section 3.
			</p>

			<h2>10. Governing law</h2>
			<p>These Terms are governed by the laws of United Kingdom.</p>

			<h2>11. Changes to these Terms</h2>
			<p>
				We may update these Terms from time to time. Continued use after
				changes take effect constitutes acceptance.
			</p>

			<h2>12. Contact</h2>
			<p>Questions about these Terms: support@netloganalyser.com.</p>
		</article>
	);
}